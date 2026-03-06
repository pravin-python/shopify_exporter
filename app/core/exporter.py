import pandas as pd
from io import BytesIO

def export_orders_to_csv(query_results):
    """
    Takes a list of Order/OrderItem tuples or dicts 
    and returns a BytesIO CSV buffer.
    """
    if not query_results:
        return BytesIO(b"")
    
    # Flatten the data structure
    flat_data = []
    
    # We expect query_results to be tuples from SQLAlchemy join: (Order, OrderItem)
    # Using explicit mapping to easily map to CSV
    for order, item in query_results:
        row = {
            "Shopify Order ID": str(order.shopify_order_id.split('/')[-1]) if order.shopify_order_id else "",
            "Order Name": order.order_name,
            "Order Created": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "",
            "SKU": item.sku,
            "Quantity": item.quantity,
            "Fulfilled At": item.fulfilled_at.strftime("%Y-%m-%d %H:%M:%S") if item.fulfilled_at else "",
            "Tracking Number": item.tracking_number,
            "Delivery Status": item.delivery_status,
            "Shipping Email Time": item.shipping_email_time.strftime("%Y-%m-%d %H:%M:%S") if item.shipping_email_time else ""
            "Delivered At": item.delivered_at.strftime("%Y-%m-%d %H:%M:%S") if item.delivered_at else "",
        }
        flat_data.append(row)
        
    df = pd.DataFrame(flat_data)
    
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return output
