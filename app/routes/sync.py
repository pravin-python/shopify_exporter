from flask import Blueprint, jsonify, request
from flask import current_app
from app.core.shopify_client import ShopifyClient
from app.core.usps_client import USPSClient
from app.core.bulk_parser import parse_and_store_bulk_data
from app.models.order_item import OrderItem
from app.extensions import db
from datetime import datetime

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/orders', methods=['POST'])
def sync_orders():
    """Trigger Shopify sync with optional date range."""
    store = current_app.config.get('SHOPIFY_STORE')
    token = current_app.config.get('SHOPIFY_ACCESS_TOKEN')
    
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
    
    try:
        orders = client.get_orders_with_tracking(start_date=start_date, end_date=end_date)
        print(orders)
        orders_saved = parse_and_store_bulk_data(orders)
        
        return jsonify({
            "success": True,
            "message": f"Successfully synced {orders_saved} orders.",
            "count": orders_saved
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Sync failed: {str(e)}"
        }), 400

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
