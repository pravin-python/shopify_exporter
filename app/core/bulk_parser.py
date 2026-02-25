"""
Parser for Shopify GraphQL order data.
Parses the list of order dicts from ShopifyClient.get_orders_with_tracking()
and stores them in Order + OrderItem tables with proper relationships.
"""
from datetime import datetime
from app.extensions import db
from app.models.order import Order
from app.models.order_item import OrderItem


def parse_and_store_bulk_data(orders_data):
    """
    Parse order data from Shopify GraphQL API and store in database.
    
    Expected input format (list of dicts):
    [
        {
            "order_id": "gid://shopify/Order/123",
            "order_name": "#1010",
            "order_created_at": "2025-07-29T13:27:08Z",
            "fulfillment": [...],
            "items": [
                {
                    "id": "gid://shopify/LineItem/456",
                    "title": "Product Name",
                    "quantity": 1,
                    "sku": "SKU-123" or None,
                    "variantTitle": "$10",
                    "vendor": "Vendor Name",
                    "originalUnitPriceSet": {"shopMoney": {"amount": "10.06", "currencyCode": "INR"}},
                    "totalDiscountSet": {"shopMoney": {"amount": "0.0", "currencyCode": "INR"}}
                }
            ]
        }
    ]
    
    Returns: number of orders saved/updated
    """
    orders_saved = 0

    # Clear ALL existing data before inserting fresh orders
    OrderItem.query.delete()
    Order.query.delete()
    db.session.flush()

    for order_data in orders_data:
        shopify_order_id = order_data.get('order_id', '')
        if not shopify_order_id:
            continue

        # ----- Create Order -----
        created_at_str = order_data.get('order_created_at', '')
        try:
            created_at = datetime.fromisoformat(
                created_at_str.replace('Z', '+00:00')
            ).replace(tzinfo=None)
        except (ValueError, AttributeError):
            created_at = datetime.utcnow()

        order = Order(
            shopify_order_id=shopify_order_id,
            order_name=order_data.get('order_name', ''),
            created_at=created_at,
        )
        db.session.add(order)
        db.session.flush()  # Get the DB-generated id

        # ----- Tracking numbers from fulfillments -----
        fulfillments_mapped = []
        for fulfillment in order_data.get('fulfillment', []):
            if isinstance(fulfillment, dict):
                created_at_str = fulfillment.get('createdAt', '')
                fulfilled_at = None
                if created_at_str:
                    try:
                        fulfilled_at = datetime.fromisoformat(
                            created_at_str.replace('Z', '+00:00')
                        ).replace(tzinfo=None)
                    except (ValueError, AttributeError):
                        pass

                for tracking in fulfillment.get('trackingInfo', []):
                    tn = tracking.get('number', '')
                    if tn:
                        fulfillments_mapped.append({
                            'tracking_number': tn,
                            'tracking_url': tracking.get('url'),
                            'tracking_company': tracking.get('company'),
                            'fulfilled_at': fulfilled_at
                        })

        # ----- Create Line Items -----
        items = order_data.get('items', [])
        for idx, item_data in enumerate(items):
            sku = item_data.get('sku') or item_data.get('title', 'UNKNOWN')

            tracking_info = {}
            if fulfillments_mapped:
                tracking_info = fulfillments_mapped[idx] if idx < len(fulfillments_mapped) else fulfillments_mapped[0]

            order_item = OrderItem(
                order_id=order.id,
                sku=sku,
                quantity=item_data.get('quantity', 1),
                tracking_number=tracking_info.get('tracking_number'),
                tracking_url=tracking_info.get('tracking_url'),
                tracking_company=tracking_info.get('tracking_company'),
                fulfilled_at=tracking_info.get('fulfilled_at'),
            )
            db.session.add(order_item)

        orders_saved += 1

    db.session.commit()
    return orders_saved
