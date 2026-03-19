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

sync_bp = Blueprint('sync', __name__)

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

    try:
        orders = client.get_orders_with_tracking(start_date=start_date, end_date=end_date)
        orders_saved = parse_and_store_bulk_data(orders)

        # Save sync date range to database (old sync log already truncated in bulk_parser)
        sync_log = SyncLog(
            sync_start_date=effective_start,
            sync_end_date=effective_end,
            orders_synced=orders_saved,
        )
        db.session.add(sync_log)
        db.session.commit()

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Sync failed: {str(e)}"
        }), 400

    # Start background thread to fetch email tracking events concurrently
    import threading
    import concurrent.futures
    from app.models.order import Order
    from app.routes.api import sync_status
    
    def fetch_email_events_async(app, orders_data, token):
        with app.app_context():
            sync_status["is_running"] = True
            try:
                store = app.config.get('SHOPIFY_STORE')
                local_client = ShopifyClient(store, token)
                
                # Form a dict of order_gid -> Order.id
                # DB reads happen sequentially here (before concurrent HTTP calls)
                gid_to_db_id = {}
                for order_data in orders_data:
                    order_gid = order_data["order_id"]
                    db_order = Order.query.filter_by(shopify_order_id=order_gid).first()
                    if db_order:
                        gid_to_db_id[order_gid] = db_order.id
                        
                def fetch_single_event(order_gid):
                    # Only HTTP requests run concurrently — no DB access here
                    return order_gid, local_client.get_order_shipping_email_event(order_gid)
                
                # Collect all API results first (concurrent HTTP only, no DB writes)
                email_results = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_gid = {executor.submit(fetch_single_event, gid): gid for gid in gid_to_db_id.keys()}
                    for future in concurrent.futures.as_completed(future_to_gid):
                        try:
                            order_gid, email_event = future.result()
                            if email_event:
                                email_results[order_gid] = email_event
                        except Exception as exc:
                            print(f'Order fetch generated an exception: {exc}')
                
                # Now write all results to DB sequentially (no concurrent DB access)
                for order_gid, email_event in email_results.items():
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
            except Exception as e:
                print(f'Background email sync error: {e}')
                db.session.rollback()
            finally:
                sync_status["is_running"] = False

    app_instance = current_app._get_current_object()
    thread = threading.Thread(
        target=fetch_email_events_async, 
        args=(app_instance, orders, token)
    )
    thread.start()

    return jsonify({
        "success": True,
        "message": f"Successfully synced {orders_saved} orders. Email tracking is updating in the background.",
        "count": orders_saved,
        "sync_start_date": effective_start.strftime('%d-%m-%Y %H:%M'),
        "sync_end_date": effective_end.strftime('%d-%m-%Y %H:%M'),
        "synced_at": datetime.utcnow().strftime('%d-%m-%Y %H:%M'),
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
            try:
                local_client = ShopifyClient(store, token)

                def fetch_single_event(order_gid):
                    # Only HTTP — no DB access here
                    return order_gid, local_client.get_order_shipping_email_event(order_gid)

                # Run API calls concurrently; collect results first
                email_results = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_gid = {executor.submit(fetch_single_event, gid): gid for gid in gid_to_db_id.keys()}
                    for future in concurrent.futures.as_completed(future_to_gid):
                        try:
                            order_gid, email_event = future.result()
                            if email_event:
                                email_results[order_gid] = email_event
                        except Exception as exc:
                            print(f'Email fetch exception: {exc}')

                # Write results to DB sequentially
                for order_gid, email_event in email_results.items():
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
                print(f'Email re-fetch complete: updated {len(email_results)} orders.')
            except Exception as e:
                print(f'Email re-fetch error: {e}')
                db.session.rollback()
            finally:
                sync_status["is_running"] = False

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
