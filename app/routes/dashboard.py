"""
Dashboard route — serves the main HTML page.
Data loading is handled via AJAX through the /api/orders endpoint.
"""
from flask import Blueprint, render_template, current_app
from app.models.shop import Shop


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Render the dashboard page (data loads via DataTables AJAX)."""
    shop_url = current_app.config.get('SHOPIFY_STORE', '')

    # Check if we have a stored token for this shop
    shop_connected = False
    if shop_url:
        existing = Shop.query.filter_by(shop_url=shop_url).first()
        if existing and existing.access_token:
            shop_connected = True

    return render_template(
        'dashboard.html',
        shop_url=shop_url,
        shop_connected=shop_connected,
    )
