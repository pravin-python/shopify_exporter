import os
import secrets
import requests
import hmac
import hashlib
import urllib.parse
from flask import Blueprint, request, redirect, session, current_app, jsonify
from app.models.shop import Shop
from app.extensions import db


auth_bp = Blueprint('auth', __name__)

# ---------------------------------------------------------------------------
# Shopify API version — keep this in sync with your Partner Dashboard settings
# ---------------------------------------------------------------------------
SHOPIFY_API_VERSION = "2025-01"

# Default scopes if not specified in env
DEFAULT_SCOPES = "read_orders,read_fulfillments"


# ---------------------------------------------------------------------------
# Generate Token Flow (Replaces install and callback)
# ---------------------------------------------------------------------------
@auth_bp.route("/generate_token")
def generate_token():
    """
    Generate an access token directly using client credentials.
    """
    shop = current_app.config.get("SHOPIFY_STORE")
    
    if not shop:
        return jsonify({"error": "SHOPIFY_STORE is not configured in environment."}), 500

    api_key = current_app.config.get("SHOPIFY_API_KEY")
    api_secret = current_app.config.get("SHOPIFY_API_SECRET")

    if not api_key or not api_secret:
        return jsonify({"error": "SHOPIFY_API_KEY or SHOPIFY_API_SECRET is not configured in environment."}), 500

    token_url = f"https://{shop}/admin/oauth/access_token"

    try:
        headers = {
            "Content-Type": "application/json",
        }
        response = requests.post(token_url, json={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        }, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Token generation failed: {e}")
        return jsonify({"error": f"Failed to generate token with Shopify: {str(e)}"}), 502

    data = response.json()
    access_token = data.get("access_token")
    scope = data.get("scope", "")

    if not access_token:
        return jsonify({"error": "Shopify response did not include an access_token."}), 400

    # --- Persist to database (upsert) -------------------------------------
    existing_shop = Shop.query.filter_by(shop_url=shop).first()
    if existing_shop:
        existing_shop.access_token = access_token
    else:
        new_shop = Shop(shop_url=shop, access_token=access_token)
        db.session.add(new_shop)

    db.session.commit()

    current_app.logger.info(f"✅ Access token stored for {shop} (scopes: {scope})")

    # Redirect back to dashboard with success params → triggers the success modal
    from urllib.parse import urlencode
    params = urlencode({"oauth": "success", "shop": shop, "scopes": scope})
    return redirect(f"/?{params}")


# ---------------------------------------------------------------------------
# Step 3: /status — Check if a shop has a stored token
# ---------------------------------------------------------------------------
@auth_bp.route("/status")
def status():
    """
    Quick health-check to see if an access token exists for a shop.

    Usage:
        GET /auth/status?shop=your-store.myshopify.com
    """
    shop = request.args.get("shop")
    if not shop:
        return jsonify({"error": "Missing 'shop' query parameter."}), 400

    existing = Shop.query.filter_by(shop_url=shop).first()

    return jsonify({
        "shop": shop,
        "token_stored": existing is not None,
        "created_at": existing.created_at.isoformat() if existing else None,
    })
