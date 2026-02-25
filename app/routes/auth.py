import requests
from flask import Blueprint, request, current_app, jsonify
from app.models.shop import Shop
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/callback")
def callback():
    """Handle Shopify OAuth callback, exchange code for access token, and store it."""
    shop_url = request.args.get("shop")
    code = request.args.get("code")

    if not shop_url or not code:
        return "Missing shop or code parameters.", 400

    api_key = current_app.config.get("SHOPIFY_API_KEY")
    api_secret = current_app.config.get("SHOPIFY_API_SECRET")

    if not api_key or not api_secret:
        return "API Key or Secret is not configured in environment.", 500

    url = f"https://{shop_url}/admin/oauth/access_token"

    try:
        response = requests.post(url, json={
            "client_id": api_key,
            "client_secret": api_secret,
            "code": code
        })
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Failed to exchange token with Shopify: {str(e)}", 400

    data = response.json()
    print("ACCESS TOKEN:", data)

    access_token = data.get("access_token")
    if not access_token:
        return "Could not retrieve access token from Shopify response.", 400

    # Save to SQLite Model
    shop = Shop.query.filter_by(shop_url=shop_url).first()
    if shop:
        shop.access_token = access_token
    else:
        shop = Shop(shop_url=shop_url, access_token=access_token)
        db.session.add(shop)

    db.session.commit()

    return "Done - Access token safely stored in SQLite!"
