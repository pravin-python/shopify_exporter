from flask import Blueprint, render_template, request
from app.models.order import Order
from app.models.order_item import OrderItem
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    # Get filter arguments
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sku_filter = request.args.get('sku')
    page = request.args.get('page', 1, type=int)
    
    # Base query joining Order and OrderItem
    query = Order.query.join(OrderItem, Order.id == OrderItem.order_id)
    
    # Apply filters
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
            
    # Order by creation date descending
    query = query.order_by(Order.created_at.desc())
    
    # Add pairs (Order, OrderItem) to a list query
    query = query.with_entities(Order, OrderItem)
    
    # Paginate results (e.g., 20 per page)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template(
        'dashboard.html',
        pagination=pagination,
        start_date=start_date or '',
        end_date=end_date or '',
        sku_filter=sku_filter or ''
    )
