"""
Export routes for CSV download.
Supports both 'Export All' (with filters) and 'Export Selected' (by IDs).
"""
from flask import Blueprint, request, send_file, jsonify
from app.models.order import Order
from app.models.order_item import OrderItem
from app.core.exporter import export_orders_to_csv
from datetime import datetime

export_bp = Blueprint('export', __name__)


@export_bp.route('/')
def export_csv():
    """Export all orders matching the current filters as CSV."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sku_filter = request.args.get('sku')

    query = Order.query.join(OrderItem, Order.id == OrderItem.order_id)

    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
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
    results = query.with_entities(Order, OrderItem).all()

    csv_buffer = export_orders_to_csv(results)

    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='shopify_orders_export.csv'
    )


@export_bp.route('/selected', methods=['POST'])
def export_selected():
    """Export only the selected order items (by IDs) as CSV."""
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])

    if not ids or not isinstance(ids, list):
        return jsonify({'success': False, 'message': 'No IDs provided.'}), 400

    # Sanitize IDs
    ids_list = [int(i) for i in ids if str(i).isdigit()]
    if not ids_list:
        return jsonify({'success': False, 'message': 'Invalid IDs.'}), 400

    query = (
        Order.query
        .join(OrderItem, Order.id == OrderItem.order_id)
        .filter(OrderItem.id.in_(ids_list))
        .order_by(Order.created_at.desc())
    )
    results = query.with_entities(Order, OrderItem).all()

    csv_buffer = export_orders_to_csv(results)

    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='shopify_orders_selected_export.csv'
    )
