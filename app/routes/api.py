"""
API routes for DataTables server-side processing.
Provides JSON endpoints for AJAX-powered order listing.
"""
from flask import Blueprint, request, jsonify
from app.models.order import Order
from app.models.order_item import OrderItem
from datetime import datetime

api_bp = Blueprint('api', __name__)


@api_bp.route('/orders')
def get_orders():
    """
    DataTables server-side processing endpoint.
    
    Accepts standard DataTables params:
      - draw, start, length
      - search[value] (global search)
      - order[0][column], order[0][dir] (sorting)
    
    Also accepts custom filter params:
      - start_date, end_date, sku
    
    Returns JSON in DataTables-expected format.
    """
    # DataTables params
    draw = request.args.get('draw', 1, type=int)
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', 20, type=int)
    search_value = request.args.get('search[value]', '').strip()
    order_column_idx = request.args.get('order[0][column]', 0, type=int)
    order_dir = request.args.get('order[0][dir]', 'desc')

    # Custom filter params
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    sku_filter = request.args.get('sku', '').strip()

    sortable_columns = {
        1: Order.shopify_order_id,
        2: Order.order_name,
        3: OrderItem.sku,
        4: OrderItem.quantity,
        5: Order.created_at,
        6: OrderItem.fulfilled_at,
        7: OrderItem.tracking_number,
        8: OrderItem.delivery_status,
        9: OrderItem.delivered_at,
        10: OrderItem.shipping_email_message,
        11: OrderItem.shipping_email_time,
    }

    # Base query
    query = Order.query.join(OrderItem, Order.id == OrderItem.order_id)

    # Total records (before any filter)
    total_records = query.with_entities(OrderItem.id).count()

    # Apply custom filters
    if start_date:
        try:
            query = query.filter(Order.created_at >= start_date)
        except Exception:
            pass

    if end_date:
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(
                Order.created_at <= dt_end.replace(hour=23, minute=59, second=59)
            )
        except ValueError:
            query = query.filter(Order.created_at <= end_date)

    if sku_filter:
        skus = [s.strip() for s in sku_filter.split(',') if s.strip()]
        if skus:
            query = query.filter(OrderItem.sku.in_(skus))

    # Apply global search (across key text columns)
    if search_value:
        search_pattern = f"%{search_value}%"
        query = query.filter(
            (Order.order_name.ilike(search_pattern)) |
            (Order.shopify_order_id.ilike(search_pattern)) |
            (OrderItem.sku.ilike(search_pattern)) |
            (OrderItem.tracking_number.ilike(search_pattern)) |
            (OrderItem.delivery_status.ilike(search_pattern))
        )

    # Filtered count (after filters, before pagination)
    filtered_records = query.with_entities(OrderItem.id).count()

    # Sorting
    sort_col = sortable_columns.get(order_column_idx, Order.created_at)
    if order_dir == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Select both entities
    query = query.with_entities(Order, OrderItem)

    # Pagination
    results = query.offset(start).limit(length).all()

    # Build response data
    data = []
    for order, item in results:
        data.append({
            'item_id': item.id,
            'order_id': order.shopify_order_id.split('/')[-1] if order.shopify_order_id else '',
            'order_name': order.order_name or '',
            'sku': item.sku or '',
            'quantity': item.quantity or 0,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else '',
            'fulfilled_at': item.fulfilled_at.strftime('%Y-%m-%d %H:%M') if item.fulfilled_at else '',
            'tracking_number': item.tracking_number or '',
            'delivery_status': item.delivery_status or 'Pending',
            'delivered_at': item.delivered_at.strftime('%Y-%m-%d %H:%M') if item.delivered_at else '',
            'shipping_email_message': item.shipping_email_message or '',
            'shipping_email_time': item.shipping_email_time.strftime('%Y-%m-%d %H:%M') if item.shipping_email_time else '',
        })

    return jsonify({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data,
    })


@api_bp.route('/orders/all-ids')
def get_all_matching_ids():
    """
    Returns all OrderItem IDs matching the current filters.
    Used for 'Select All (All Pages)' feature.
    """
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    sku_filter = request.args.get('sku', '').strip()
    search_value = request.args.get('search', '').strip()

    query = Order.query.join(OrderItem, Order.id == OrderItem.order_id)

    if start_date:
        try:
            query = query.filter(Order.created_at >= start_date)
        except Exception:
            pass

    if end_date:
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(
                Order.created_at <= dt_end.replace(hour=23, minute=59, second=59)
            )
        except ValueError:
            query = query.filter(Order.created_at <= end_date)

    if sku_filter:
        skus = [s.strip() for s in sku_filter.split(',') if s.strip()]
        if skus:
            query = query.filter(OrderItem.sku.in_(skus))

    if search_value:
        search_pattern = f"%{search_value}%"
        query = query.filter(
            (Order.order_name.ilike(search_pattern)) |
            (Order.shopify_order_id.ilike(search_pattern)) |
            (OrderItem.sku.ilike(search_pattern)) |
            (OrderItem.tracking_number.ilike(search_pattern)) |
            (OrderItem.delivery_status.ilike(search_pattern))
        )

    ids = [row[0] for row in query.with_entities(OrderItem.id).all()]

    return jsonify({'ids': ids, 'count': len(ids)})
