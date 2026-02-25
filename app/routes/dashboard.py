"""
Dashboard route — serves the main HTML page.
Data loading is handled via AJAX through the /api/orders endpoint.
"""
from flask import Blueprint, render_template

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Render the dashboard page (data loads via DataTables AJAX)."""
    return render_template('dashboard.html')
