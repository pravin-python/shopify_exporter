import requests
import hmac
import hashlib
from flask import Blueprint, request, current_app, jsonify
from app.models.shop import Shop
from app.extensions import db


auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/callback")
def callback():
    """Handle Shopify OAuth callback, exchange code for access token, and store it."""
    params = request.args.to_dict()
    shop = params.get("shop")
    code = params.get("code")
    hmac_header = params.get("hmac")
    state = params.get("state")

    # 1. Verify HMAC (Crucial for security)
    # Remove 'hmac' from params to calculate hash of the rest
    data_to_verify = params.copy()
    data_to_verify.pop("hmac")

    if not shop or not code:
        return "Missing shop or code parameters.", 400
    
    # Sort keys alphabetically and join as key=value&key=value
    message = "&".join([f"{k}={v}" for k, v in sorted(data_to_verify.items())])
    api_key = current_app.config.get("SHOPIFY_API_KEY")
    api_secret = current_app.config.get("SHOPIFY_API_SECRET")

    hash_digest = hmac.new(
        api_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(hash_digest, hmac_header):
        return "HMAC validation failed", 401

    if not api_key or not api_secret:
        return "API Key or Secret is not configured in environment.", 500

    url = f"https://{shop}/admin/oauth/access_token"

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
    existing_shop = Shop.query.filter_by(shop_url=shop).first()
    if existing_shop:
        existing_shop.access_token = access_token
    else:
        new_shop = Shop(shop_url=shop, access_token=access_token)
        db.session.add(new_shop)

    db.session.commit()

    return "Done - Access token safely stored in SQLite!"
