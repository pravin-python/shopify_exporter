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
# Step 1: /install — Start the OAuth flow
# ---------------------------------------------------------------------------
@auth_bp.route("/install")
def install():
    """
    Build the Shopify OAuth authorization URL and redirect the merchant
    to grant permissions.

    Usage:
        GET /auth/install?shop=your-store.myshopify.com
    """
    shop = request.args.get("shop")
    if not shop:
        return jsonify({"error": "Missing 'shop' query parameter. "
                        "Example: /auth/install?shop=your-store.myshopify.com"}), 400

    # Sanitize — always force *.myshopify.com
    if not shop.endswith(".myshopify.com"):
        return jsonify({"error": "Invalid shop domain. Must end with .myshopify.com"}), 400

    api_key = current_app.config.get("SHOPIFY_API_KEY")
    if not api_key:
        return jsonify({"error": "SHOPIFY_API_KEY is not configured in environment."}), 500

    scopes = os.environ.get("SHOPIFY_SCOPES", DEFAULT_SCOPES)
    redirect_uri = os.environ.get(
        "SHOPIFY_REDIRECT_URI",
        request.url_root.rstrip("/") + "/auth/callback"
    )

    # Generate a cryptographically secure nonce to prevent CSRF
    nonce = secrets.token_hex(16)
    session["oauth_nonce"] = nonce
    session["oauth_shop"] = shop

    # Offline access is the default grant mode (no grant_options[] parameter)
    params = {
        "client_id": api_key,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": nonce,
    }

    auth_url = f"https://{shop}/admin/oauth/authorize?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


# ---------------------------------------------------------------------------
# Step 2: /callback — Handle redirect from Shopify, exchange code for token
# ---------------------------------------------------------------------------
@auth_bp.route("/callback")
def callback():
    """
    Shopify redirects here after the merchant approves the app.
    We exchange the authorization code for a permanent offline access token.
    """
    params = request.args.to_dict()
    shop = params.get("shop")
    code = params.get("code")
    hmac_header = params.get("hmac")
    state = params.get("state")

    # --- Basic validation ------------------------------------------------
    if not shop or not code:
        return jsonify({"error": "Missing shop or code parameters."}), 400

    api_key = current_app.config.get("SHOPIFY_API_KEY")
    api_secret = current_app.config.get("SHOPIFY_API_SECRET")

    if not api_key or not api_secret:
        return jsonify({"error": "SHOPIFY_API_KEY or SHOPIFY_API_SECRET is "
                        "not configured in environment."}), 500

    # --- State / nonce verification (CSRF protection) ---------------------
    expected_nonce = session.pop("oauth_nonce", None)
    if not state or state != expected_nonce:
        return jsonify({"error": "State (nonce) mismatch — possible CSRF attack."}), 403

    # --- HMAC verification ------------------------------------------------
    data_to_verify = {k: v for k, v in params.items() if k != "hmac"}
    message = "&".join(f"{k}={v}" for k, v in sorted(data_to_verify.items()))

    hash_digest = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(hash_digest, hmac_header or ""):
        return jsonify({"error": "HMAC validation failed — request may be tampered."}), 401

    # --- Exchange authorization code for offline access token -------------
    token_url = f"https://{shop}/admin/oauth/access_token"

    try:
        headers = {
            "Content-Type": "application/json",
        }
        response = requests.post(token_url, json={
            "client_id": api_key,
            "client_secret": api_secret,
            "code": code
        }, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Token exchange failed: {e}")
        return jsonify({"error": f"Failed to exchange token with Shopify: {str(e)}"}), 502

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
