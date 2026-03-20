import pandas as pd
from io import BytesIO
from datetime import datetime


# Target format for all dates in CSV
DATE_FORMAT = "%d-%m-%Y %H:%M"

# Common date string formats to try when parsing string dates
_DATE_PARSE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",       # ISO with timezone: 2025-07-29T13:27:08+00:00
    "%Y-%m-%dT%H:%M:%SZ",        # ISO with Z:        2025-07-29T13:27:08Z
    "%Y-%m-%dT%H:%M:%S",         # ISO without tz:    2025-07-29T13:27:08
    "%Y-%m-%d %H:%M:%S",         # Standard:          2025-07-29 13:27:08
    "%Y-%m-%d %H:%M",            # Without seconds:   2025-07-29 13:27
    "%Y-%m-%d",                  # Date only:         2025-07-29
    "%d-%m-%Y %H:%M:%S",         # DD-MM-YYYY:        29-07-2025 13:27:08
    "%d-%m-%Y %H:%M",            # DD-MM-YYYY:        29-07-2025 13:27
    "%d-%m-%Y",                  # DD-MM-YYYY:        29-07-2025
    "%d/%m/%Y %I:%M:%S %p",      # 12-hour with AM/PM: 29/7/2025 1:27:08 PM
    "%d/%m/%Y %H:%M:%S",         # 24-hour:           29/7/2025 13:27:08
    "%d/%m/%Y %H:%M",            # 24-hour short:     29/7/2025 13:27
    "%d/%m/%Y",                  # Date only:         29/7/2025
    "%m/%d/%Y %I:%M:%S %p",      # US 12-hour:        7/29/2025 1:27:08 PM
    "%m/%d/%Y %H:%M:%S",         # US 24-hour:        7/29/2025 13:27:08
    "%m/%d/%Y %H:%M",            # US 24-hour short:  7/29/2025 13:27
    "%m/%d/%Y",                  # US date only:      7/29/2025
]


def format_date(value):
    """
    Normalize any date value (datetime object or string) to DD-MM-YYYY HH:MM format.
    Returns empty string if value is None/empty or unparseable.
    """
    if not value:
        return ""

    # Already a proper datetime object
    if isinstance(value, datetime):
        return value.strftime(DATE_FORMAT)

    # It's a string — try parsing with known formats
    date_str = str(value).strip()
    if not date_str:
        return ""

    for fmt in _DATE_PARSE_FORMATS:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime(DATE_FORMAT)
        except ValueError:
            continue

    # Last resort: try fromisoformat (handles many ISO variants)
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime(DATE_FORMAT)
    except (ValueError, AttributeError):
        pass

    # Could not parse — return the raw value as-is
    return date_str


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
            "Order Created": format_date(order.created_at),
            "SKU": item.sku,
            "Quantity": item.quantity,
            "Fulfilled At": format_date(item.fulfilled_at),
            "Tracking Number": item.tracking_number,
            "Delivery Status": item.delivery_status,
            "Delivered At": format_date(item.shipping_email_time),
        }
        flat_data.append(row)
        
    df = pd.DataFrame(flat_data)
    
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return output
