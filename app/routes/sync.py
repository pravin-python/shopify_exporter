from flask import Blueprint, jsonify, request
from flask import current_app
from app.core.shopify_client import ShopifyClient
from app.core.usps_client import USPSClient
from app.core.bulk_parser import parse_and_store_bulk_data
from app.models.order_item import OrderItem
from app.models.shop import Shop
from app.models.sync_log import SyncLog
from app.extensions import db
from datetime import datetime, timedelta

class SyncCancelledException(Exception):
    pass

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/cancel', methods=['POST'])
def cancel_sync():
    """Request cancellation of the currently running background sync."""
    from app.routes.api import sync_status
    if sync_status["is_running"]:
        sync_status["cancel_requested"] = True
        return jsonify({"success": True, "message": "Cancellation requested. Finishing current batch..."})
    return jsonify({"success": False, "message": "No sync is currently running."}), 400

@sync_bp.route('/orders', methods=['POST'])
def sync_orders():
    """Trigger Shopify sync with optional date range."""
    store = current_app.config.get('SHOPIFY_STORE')

    # Fetch access token from DB first, fallback to config/env
    token = None
    if store:
        shop_record = Shop.query.filter_by(shop_url=store).first()
        if shop_record:
            token = shop_record.access_token

    if not token:
        token = current_app.config.get('SHOPIFY_ACCESS_TOKEN')

    if not token:
        return jsonify({"success": False, "message": "No access token found. Please connect Shopify first."}), 400
    client = ShopifyClient(store, token)
    
    # Parse optional date range from request body
    data = request.get_json(silent=True) or {}
    start_date = None
    end_date = None
    
    if data.get('start_date'):
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        except ValueError:
            pass
            
    if data.get('end_date'):
        try:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
    
    # Calculate effective dates (same defaults as ShopifyClient)
    effective_start = start_date if start_date else (datetime.utcnow() - timedelta(days=7))
    effective_end = end_date if end_date else datetime.utcnow()

    from app.routes.api import sync_status

    if sync_status["is_running"]:
        return jsonify({"success": False, "message": "A background sync is already running. Please wait."}), 409

    # Start background thread to run the entire sync safely
    import threading
    import concurrent.futures
    from app.models.order import Order
    
    def run_full_sync_background(app_instance, store, token, start_date, end_date, effective_start, effective_end):
        with app_instance.app_context():
            from app.routes.api import sync_status
            from app.core.shopify_client import ShopifyClient
            from app.core.bulk_parser import parse_and_store_bulk_data
            from app.models.sync_log import SyncLog
            from app.models.order import Order
            from app.models.order_item import OrderItem
            from app.extensions import db
            import concurrent.futures

            sync_status["is_running"] = True
            sync_status["cancel_requested"] = False
            sync_status["phase"] = "orders"
            sync_status["message"] = "Fetching Shopify Orders..."
            sync_status["details"] = {}
            sync_status["current_count"] = 0
            sync_status["sync_start_date"] = effective_start.strftime('%d-%m-%Y')
            sync_status["sync_end_date"] = effective_end.strftime('%d-%m-%Y')

            client = ShopifyClient(store, token)

            try:
                # 1. Clear old SyncLogs and create the live-updating one instantly
                SyncLog.query.delete()
                
                live_sync_log = SyncLog(
                    sync_start_date=effective_start,
                    sync_end_date=effective_end,
                    orders_synced=0,
                )
                db.session.add(live_sync_log)
                db.session.commit()
                live_sync_log_id = live_sync_log.id

                page_count = 0
                total_orders_saved = 0

                def stream_page_to_db(page_orders):
                    if sync_status["cancel_requested"]:
                        sync_status["message"] = "Stopping..."
                        raise SyncCancelledException("Sync manually cancelled by user.")

                    nonlocal page_count, total_orders_saved
                    page_count += 1
                    clear_db = (page_count == 1)
                    orders_saved_in_page = parse_and_store_bulk_data(page_orders, clear_existing=clear_db)
                    total_orders_saved += orders_saved_in_page

                    # Update the live UI polling count and the database SyncLog
                    sync_status["current_count"] = total_orders_saved
                    
                    log_record = db.session.get(SyncLog, live_sync_log_id)
                    if log_record:
                        log_record.orders_synced = total_orders_saved
                        db.session.commit()

                # Phase 1: Fetch and stream orders directly into DB page by page
                total_orders = client.get_orders_with_tracking(
                    start_date=start_date, 
                    end_date=end_date,
                    on_page_fetched=stream_page_to_db,
                    cancel_check=lambda: sync_status["cancel_requested"],
                )

                # Phase 2: Emails
                sync_status["phase"] = "emails"
                sync_status["message"] = "Fetching Email Events..."

                # We need the full list of order GIDs for the background email fetch
                orders_just_saved = []
                if total_orders_saved > 0:
                    orders_just_saved = [{"order_id": row.shopify_order_id} for row in Order.query.with_entities(Order.shopify_order_id).all()]

                if orders_just_saved:
                    gid_to_db_id = {}
                    for order_data in orders_just_saved:
                        order_gid = order_data["order_id"]
                        db_order = Order.query.filter_by(shopify_order_id=order_gid).first()
                        if db_order:
                            gid_to_db_id[order_gid] = db_order.id
                            
                    def fetch_single_event(order_gid):
                        if sync_status["cancel_requested"]:
                            return order_gid, None
                        return order_gid, client.get_order_shipping_email_event(order_gid)
                    
                    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
                    try:
                        future_to_gid = {executor.submit(fetch_single_event, gid): gid for gid in gid_to_db_id.keys()}
                        for future in concurrent.futures.as_completed(future_to_gid):
                            if sync_status["cancel_requested"]:
                                sync_status["message"] = "Stopping Emails..."
                                executor.shutdown(wait=False, cancel_futures=True)
                                raise SyncCancelledException("Email sync cancelled by user.")
                            
                            try:
                                order_gid, email_event = future.result()
                                if email_event:
                                    db_order_id = gid_to_db_id[order_gid]
                                    items = OrderItem.query.filter_by(order_id=db_order_id).all()
                                    for item in items:
                                        item.shipping_email_message = email_event["message"]
                                        try:
                                            item.shipping_email_time = datetime.fromisoformat(
                                                email_event["createdAt"].replace('Z', '+00:00')
                                            ).replace(tzinfo=None)
                                        except (ValueError, AttributeError):
                                            pass
                                    db.session.commit()
                            except Exception as exc:
                                print(f'Order fetch generated an exception: {exc}')
                    finally:
                        executor.shutdown(wait=False)

                # Export details to the UI polling mechanism
                sync_status["details"] = {
                    "count": total_orders_saved,
                    "sync_start_date": effective_start.strftime('%d-%m-%Y %H:%M'),
                    "sync_end_date": effective_end.strftime('%d-%m-%Y %H:%M'),
                    "synced_at": datetime.utcnow().strftime('%d-%m-%Y %H:%M')
                }
            except SyncCancelledException as e:
                print(f"Background sync cancelled: {e}")
                sync_status["details"] = {}  # Don't update banner if cancelled
            except Exception as e:
                print(f"Background sync error: {e}")
                db.session.rollback()
            finally:
                sync_status["is_running"] = False
                sync_status["cancel_requested"] = False
                sync_status["phase"] = ""
                sync_status["message"] = ""

    app_instance = current_app._get_current_object()
    thread = threading.Thread(
        target=run_full_sync_background, 
        args=(app_instance, store, token, start_date, end_date, effective_start, effective_end)
    )
    thread.start()

    return jsonify({
        "success": True,
        "message": f"Sync started in the background."
    })

@sync_bp.route('/emails', methods=['POST'])
def sync_emails():
    """Re-fetch shipping email events for all orders already stored in the DB."""
    import threading
    import concurrent.futures
    from app.models.order import Order
    from app.routes.api import sync_status

    # Don't allow starting a new job if one is already running
    if sync_status["is_running"]:
        return jsonify({"success": False, "message": "A background sync is already running. Please wait."}), 409

    store = current_app.config.get('SHOPIFY_STORE')

    # Fetch access token
    token = None
    if store:
        shop_record = Shop.query.filter_by(shop_url=store).first()
        if shop_record:
            token = shop_record.access_token
    if not token:
        token = current_app.config.get('SHOPIFY_ACCESS_TOKEN')
    if not token:
        return jsonify({"success": False, "message": "No access token found. Please connect Shopify first."}), 400

    # Read all order GIDs from DB (sequential, before background thread starts)
    orders_in_db = Order.query.with_entities(Order.id, Order.shopify_order_id).all()
    gid_to_db_id = {row.shopify_order_id: row.id for row in orders_in_db if row.shopify_order_id}

    if not gid_to_db_id:
        return jsonify({"success": False, "message": "No orders found in the database."}), 404

    def fetch_emails_background(app, gid_to_db_id, store, token):
        with app.app_context():
            sync_status["is_running"] = True
            sync_status["cancel_requested"] = False
            sync_status["phase"] = "emails"
            sync_status["message"] = "Fetching Email Events..."
            try:
                local_client = ShopifyClient(store, token)

                def fetch_single_event(order_gid):
                    # Skip API call if cancel was already requested
                    if sync_status["cancel_requested"]:
                        return order_gid, None
                    return order_gid, local_client.get_order_shipping_email_event(order_gid)

                # Run API calls concurrently and stream results to DB individually
                updated_count = 0
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
                try:
                    future_to_gid = {executor.submit(fetch_single_event, gid): gid for gid in gid_to_db_id.keys()}
                    for future in concurrent.futures.as_completed(future_to_gid):
                        if sync_status["cancel_requested"]:
                            sync_status["message"] = "Stopping Emails..."
                            executor.shutdown(wait=False, cancel_futures=True)
                            raise SyncCancelledException("Email sync cancelled by user.")

                        try:
                            order_gid, email_event = future.result()
                            if email_event:
                                db_order_id = gid_to_db_id[order_gid]
                                items = OrderItem.query.filter_by(order_id=db_order_id).all()
                                for item in items:
                                    item.shipping_email_message = email_event["message"]
                                    try:
                                        item.shipping_email_time = datetime.fromisoformat(
                                            email_event["createdAt"].replace('Z', '+00:00')
                                        ).replace(tzinfo=None)
                                    except (ValueError, AttributeError):
                                        pass
                                db.session.commit()
                                updated_count += 1
                        except Exception as exc:
                            print(f'Email fetch exception: {exc}')
                finally:
                    executor.shutdown(wait=False)

                print(f'Email re-fetch complete: updated {updated_count} orders.')
            except SyncCancelledException as e:
                print(f"Email sync cancelled: {e}")
            except Exception as e:
                print(f'Email re-fetch error: {e}')
                db.session.rollback()
            finally:
                sync_status["is_running"] = False
                sync_status["cancel_requested"] = False
                sync_status["phase"] = ""
                sync_status["message"] = ""

    app_instance = current_app._get_current_object()
    thread = threading.Thread(
        target=fetch_emails_background,
        args=(app_instance, gid_to_db_id, store, token)
    )
    thread.start()

    return jsonify({
        "success": True,
        "message": f"Re-fetching emails for {len(gid_to_db_id)} orders in the background.",
        "count": len(gid_to_db_id),
    })


@sync_bp.route('/delivery', methods=['POST'])

def sync_delivery():
    """Sync delivery statuses for items with tracking numbers."""
    user_id = current_app.config['USPS_USER_ID']
    client = USPSClient(user_id)
    
    # Find items that have a tracking number but aren't delivered yet
    pending_items = OrderItem.query.filter(
        OrderItem.tracking_number.isnot(None),
        OrderItem.delivery_status != 'Delivered'
    ).all()
    
    updated_count = 0
    tracking_numbers = []
    for item in pending_items:
        tracking_numbers.append(item.tracking_number)
    
    result = client.get_bulk_delivery_status(tracking_numbers)  
    
    for item in pending_items:
        for result_item in result:
            if item.tracking_number == result_item['tracking_number']:
                item.delivery_status = result_item['status']
                item.delivered_at = result_item['delivered_at']
                updated_count += 1
        
    db.session.commit()
    return jsonify({"success": True, "message": f"Updated {updated_count} delivery statuses.", "count": updated_count})
