import json
from datetime import datetime
from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem

def parse_and_store_bulk_data(jsonl_data):
    """
    Parse JSONL data from Shopify bulk operation and store it in SQLite.
    In this mock version, jsonl_data is a list of dicts.
    """
    orders_map = {}
    
    # Pass 1: Handle orders
    for line in jsonl_data:
        if line.get("__parentId") is None and "Order" in line.get("id", ""):
            shopify_order_id = line["id"]
            
            order = Order.query.filter_by(shopify_order_id=shopify_order_id).first()
            if not order:
                created_at_str = line["createdAt"]
                # Parse naive datetime (strip timezone for simple SQLite setup)
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                
                order = Order(
                    shopify_order_id=shopify_order_id,
                    order_name=line["name"],
                    created_at=created_at
                )
                db.session.add(order)
                db.session.flush() # Get DB ID
                
            orders_map[shopify_order_id] = order.id

    # Pass 2: Handle LineItems
    for line in jsonl_data:
        parent_id = line.get("__parentId")
        if parent_id and parent_id in orders_map:
            order_id = orders_map[parent_id]
            
            item = OrderItem(
                order_id=order_id,
                sku=line.get("sku", "UNKNOWN"),
                quantity=line.get("quantity", 1),
                tracking_number=f"TRK{line.get('id', '')[-5:]}"  # Mock a tracking number
            )
            db.session.add(item)

    db.session.commit()
    return len(orders_map)
