from flask import Blueprint, request, send_file
from app.models.order import Order
from app.models.order_item import OrderItem
from app.core.exporter import export_orders_to_csv
from datetime import datetime

export_bp = Blueprint('export', __name__)

@export_bp.route('/')
def export_csv():
    # Get same filters as dashboard
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sku_filter = request.args.get('sku')
    
    query = Order.query.join(OrderItem, Order.id == OrderItem.order_id)
    
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        # Include the whole end day by adding 23:59:59
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(Order.created_at <= dt_end.replace(hour=23, minute=59, second=59))
        except ValueError:
            query = query.filter(Order.created_at <= end_date)
            
    if sku_filter:
        skus = [s.strip() for s in sku_filter.split(',') if s.strip()]
        if skus:
            query = query.filter(OrderItem.sku.in_(skus))
            
    query = query.order_by(Order.created_at.desc())
    
    # Add pairs (Order, OrderItem) to a list
    results = query.with_entities(Order, OrderItem).all()
    
    csv_buffer = export_orders_to_csv(results)
    
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='shopify_orders_export.csv'
    )
