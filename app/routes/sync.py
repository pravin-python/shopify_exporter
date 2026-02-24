from flask import Blueprint, jsonify
from flask import current_app
from app.core.shopify_client import ShopifyClient
from app.core.usps_client import USPSClient
from app.core.bulk_parser import parse_and_store_bulk_data
from app.models.order_item import OrderItem
from app.extensions import db

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/orders', methods=['POST'])
def sync_orders():
    """Trigger Shopify sync."""
    store = current_app.config['SHOPIFY_STORE']
    token = current_app.config['SHOPIFY_ACCESS_TOKEN']
    
    client = ShopifyClient(store, token)
    
    # 1. Trigger bulk
    operation = client.trigger_bulk_orders_export()
    
    # 2. Mock wait/check
    status = client.check_bulk_operation_status(operation['bulk_operation_id'])
    
    if status['status'] == 'COMPLETED':
        # 3. Download data
        data = client.download_bulk_data(status['url'])
        
        # 4. Parse and store
        orders_saved = parse_and_store_bulk_data(data)
        
        return jsonify({"success": True, "message": f"Successfully synced {orders_saved} orders.", "count": orders_saved})
    
    return jsonify({"success": False, "message": "Sync failed or still running."}), 400

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
    for item in pending_items:
        # Mocking check
        result = client.check_delivery_status(item.tracking_number)
        
        item.delivery_status = result['status']
        if result['delivered_at']:
            item.delivered_at = result['delivered_at']
        
        updated_count += 1
        
    db.session.commit()
    return jsonify({"success": True, "message": f"Updated {updated_count} delivery statuses.", "count": updated_count})
