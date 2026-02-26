# Shopify OAuth — Offline Access Token Guide

> **Shopify API Version**: `2025-01` (latest stable)
> **Framework**: Flask + `requests`
> **Token Type**: Offline access token (`shpat_xxxxxxxx`)

---

## Table of Contents

1. [How Offline Tokens Work](#1-how-offline-tokens-work)
2. [Partner Dashboard Setup](#2-partner-dashboard-setup)
3. [Environment Variables](#3-environment-variables)
4. [Complete OAuth Flow (3 Steps)](#4-complete-oauth-flow)
5. [Fetching Orders via Admin REST API](#5-fetching-orders-via-admin-rest-api)
6. [Fetching Fulfillments](#6-fetching-fulfillments)
7. [MCP Integration for Token Management](#7-mcp-integration-for-token-management)
8. [Security Best Practices](#8-security-best-practices)
9. [Common Mistakes to Avoid](#9-common-mistakes-to-avoid)

---

## 1. How Offline Tokens Work

Shopify issues two kinds of access tokens:

| Feature | **Offline** (what we want) | Online |
|---|---|---|
| Token prefix | `shpat_` | `shpua_` |
| Lifetime | Permanent (until uninstalled) | ~24 hours |
| Tied to | App installation | Individual user session |
| Use-case | Background jobs, syncing | Real-time admin UI |

**Offline tokens** are generated through the standard OAuth 2.0 authorization code grant.
They **do not expire** as long as the app stays installed on the store.

### OAuth Flow Overview

```
┌──────────┐       ┌──────────┐       ┌──────────────┐
│ Merchant │       │ Your App │       │   Shopify    │
│ (Browser)│       │ (Flask)  │       │   Servers    │
└────┬─────┘       └────┬─────┘       └──────┬───────┘
     │  1. Install       │                     │
     │ ─────────────────>│                     │
     │                   │  2. Redirect to     │
     │ <─────────────────│  Shopify consent    │
     │                   │                     │
     │  3. Grant         │                     │
     │ ──────────────────────────────────────> │
     │                   │                     │
     │                   │  4. Redirect back   │
     │                   │ <───────────────────│
     │                   │   (with ?code=xxx)  │
     │                   │                     │
     │                   │  5. POST exchange   │
     │                   │ ───────────────────>│
     │                   │                     │
     │                   │  6. { access_token } │
     │                   │ <───────────────────│
     │                   │                     │
     │  7. "Done!"       │                     │
     │ <─────────────────│                     │
```

---

## 2. Partner Dashboard Setup

1. Go to [Shopify Partners](https://partners.shopify.com/) → **Apps** → your app.
2. Under **App setup → URLs**:
   - **App URL**: `http://localhost:5000/auth/install`
   - **Allowed redirection URL(s)**: `http://localhost:5000/auth/callback`
3. Under **API credentials**, copy:
   - **API key** → `SHOPIFY_API_KEY`
   - **API secret key** → `SHOPIFY_API_SECRET`

> ⚠️ For production, replace `localhost` with your public HTTPS domain.

---

## 3. Environment Variables

### `.env` file structure

```env
# Flask configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=generate-a-random-secret-key-here

# Shopify configuration
SHOPIFY_STORE=your-store-name.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Shopify OAuth (from Partner Dashboard → App → API credentials)
SHOPIFY_API_KEY=your-app-api-key
SHOPIFY_API_SECRET=your-app-api-secret-key
SHOPIFY_SCOPES=read_orders,read_fulfillments
SHOPIFY_REDIRECT_URI=http://localhost:5000/auth/callback

# USPS configuration (optional)
USPS_USER_ID=xxxxxxx
```

| Variable | Source | Required |
|---|---|---|
| `SHOPIFY_API_KEY` | Partner Dashboard → API credentials | ✅ For OAuth |
| `SHOPIFY_API_SECRET` | Partner Dashboard → API credentials | ✅ For OAuth |
| `SHOPIFY_SCOPES` | Your app's permission needs | ✅ For OAuth |
| `SHOPIFY_REDIRECT_URI` | Must match Partner Dashboard | ✅ For OAuth |
| `SHOPIFY_ACCESS_TOKEN` | Generated after OAuth completes | ✅ For API calls |
| `SHOPIFY_STORE` | The `*.myshopify.com` domain | ✅ For API calls |

---

## 4. Complete OAuth Flow

### Step 1: Installation URL (`/auth/install`)

The merchant visits this URL to begin installing your app.

```python
@auth_bp.route("/install")
def install():
    """
    Build the Shopify OAuth authorization URL and redirect the
    merchant to Shopify's consent screen.

    Usage:
        GET /auth/install?shop=your-store.myshopify.com
    """
    shop = request.args.get("shop")
    if not shop:
        return jsonify({"error": "Missing 'shop' query parameter."}), 400

    if not shop.endswith(".myshopify.com"):
        return jsonify({"error": "Invalid shop domain."}), 400

    api_key = current_app.config.get("SHOPIFY_API_KEY")
    scopes = os.environ.get("SHOPIFY_SCOPES", "read_orders,read_fulfillments")
    redirect_uri = os.environ.get(
        "SHOPIFY_REDIRECT_URI",
        request.url_root.rstrip("/") + "/auth/callback"
    )

    # Cryptographic nonce to prevent CSRF
    nonce = secrets.token_hex(16)
    session["oauth_nonce"] = nonce
    session["oauth_shop"] = shop

    params = {
        "client_id": api_key,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": nonce,
        # No grant_options[] → defaults to OFFLINE access
    }

    auth_url = f"https://{shop}/admin/oauth/authorize?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)
```

**Try it**: Open your browser to:

```
http://localhost:5000/auth/install?shop=your-store.myshopify.com
```

### Step 2: Redirect URL Handling (`/auth/callback`)

After the merchant approves, Shopify redirects back with `?code=...&hmac=...&state=...`.

```python
@auth_bp.route("/callback")
def callback():
    params = request.args.to_dict()
    shop = params.get("shop")
    code = params.get("code")
    hmac_header = params.get("hmac")
    state = params.get("state")

    # Validate required params
    if not shop or not code:
        return jsonify({"error": "Missing shop or code parameters."}), 400

    api_key = current_app.config.get("SHOPIFY_API_KEY")
    api_secret = current_app.config.get("SHOPIFY_API_SECRET")

    if not api_key or not api_secret:
        return jsonify({"error": "API Key/Secret not configured."}), 500

    # ── CSRF protection: verify nonce ─────────────────────────
    expected_nonce = session.pop("oauth_nonce", None)
    if not state or state != expected_nonce:
        return jsonify({"error": "State mismatch — possible CSRF."}), 403

    # ── HMAC verification ─────────────────────────────────────
    data_to_verify = {k: v for k, v in params.items() if k != "hmac"}
    message = "&".join(f"{k}={v}" for k, v in sorted(data_to_verify.items()))

    hash_digest = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(hash_digest, hmac_header or ""):
        return jsonify({"error": "HMAC validation failed."}), 401
```

### Step 3: Exchange Authorization Code for Access Token

```python
    # ── Exchange code for permanent offline token ─────────────
    token_url = f"https://{shop}/admin/oauth/access_token"

    response = requests.post(token_url, json={
        "client_id": api_key,
        "client_secret": api_secret,
        "code": code,
    }, timeout=15)
    response.raise_for_status()

    data = response.json()
    access_token = data.get("access_token")  # e.g. "shpat_abc123..."
    scope = data.get("scope", "")

    # ── Save to database ──────────────────────────────────────
    existing_shop = Shop.query.filter_by(shop_url=shop).first()
    if existing_shop:
        existing_shop.access_token = access_token
    else:
        new_shop = Shop(shop_url=shop, access_token=access_token)
        db.session.add(new_shop)

    db.session.commit()

    # Now SHOPIFY_ACCESS_TOKEN = access_token (shpat_xxxxx)
```

**Response from Shopify** (what `data` looks like):

```json
{
    "access_token": "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",
    "scope": "read_orders,read_fulfillments"
}
```

### Storing the Token

The token is stored via two mechanisms:

| Method | How | Best for |
|---|---|---|
| **SQLite (database)** | `Shop` model with `shop_url` + `access_token` | Multi-store apps |
| **`.env` file** | `SHOPIFY_ACCESS_TOKEN=shpat_xxx` | Single-store tools |

For a single-store internal tool, you can copy the token from the OAuth response and paste it into your `.env` file:

```env
SHOPIFY_ACCESS_TOKEN=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
```

---

## 5. Fetching Orders via Admin REST API

Once you have the access token, you can call any Admin API endpoint.

### List all orders

```python
import requests
import os

SHOPIFY_STORE = os.environ["SHOPIFY_STORE"]
SHOPIFY_ACCESS_TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]
API_VERSION = "2025-01"

def get_orders(status="any", limit=50):
    """
    Fetch orders from Shopify Admin REST API.

    GET /admin/api/2025-01/orders.json
    """
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/orders.json"

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    params = {
        "status": status,       # "any", "open", "closed", "cancelled"
        "limit": limit,         # max 250
        "order": "created_at DESC",
    }

    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()

    orders = response.json().get("orders", [])

    for order in orders:
        print(f"Order #{order['order_number']} — "
              f"{order['total_price']} {order['currency']} — "
              f"Status: {order['financial_status']}")

    return orders
```

### Get a single order by ID

```python
def get_order_by_id(order_id):
    """
    GET /admin/api/2025-01/orders/{order_id}.json
    """
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/orders/{order_id}.json"

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    return response.json().get("order")
```

### Pagination with Link headers

Shopify uses cursor-based pagination:

```python
def get_all_orders():
    """Fetch ALL orders using cursor-based pagination."""
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/orders.json?limit=250&status=any"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}

    all_orders = []

    while url:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        all_orders.extend(response.json().get("orders", []))

        # Parse next page from Link header
        link = response.headers.get("Link", "")
        url = None
        if 'rel="next"' in link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split("<")[1].split(">")[0]

    print(f"Total orders fetched: {len(all_orders)}")
    return all_orders
```

---

## 6. Fetching Fulfillments

### List fulfillments for an order

```python
def get_fulfillments(order_id):
    """
    GET /admin/api/2025-01/orders/{order_id}/fulfillments.json
    """
    url = (f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}"
           f"/orders/{order_id}/fulfillments.json")

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    fulfillments = response.json().get("fulfillments", [])

    for f in fulfillments:
        print(f"  Fulfillment #{f['id']}")
        print(f"    Status:   {f['status']}")
        print(f"    Tracking: {f.get('tracking_number', 'N/A')}")
        print(f"    Company:  {f.get('tracking_company', 'N/A')}")
        print(f"    URL:      {f.get('tracking_url', 'N/A')}")
        print()

    return fulfillments
```

### Full example: Orders + Fulfillments together

```python
def sync_orders_with_fulfillments():
    """Fetch orders and their fulfillment details."""
    orders = get_orders(status="any", limit=10)

    for order in orders:
        print(f"\n{'='*60}")
        print(f"Order #{order['order_number']} | {order['name']}")
        print(f"  Created:  {order['created_at']}")
        print(f"  Status:   {order['fulfillment_status'] or 'unfulfilled'}")
        print(f"  Total:    {order['total_price']} {order['currency']}")

        if order.get("fulfillments"):
            for f in order["fulfillments"]:
                print(f"  📦 Fulfillment: {f['status']} "
                      f"| Tracking: {f.get('tracking_number', 'N/A')}")
        else:
            # Fetch fulfillments separately if not embedded
            fulfillments = get_fulfillments(order["id"])
            if not fulfillments:
                print("  📦 No fulfillments yet")

    return orders
```

---

## 7. MCP Integration for Token Management

The **Model Context Protocol (MCP)** provides a standardized way for AI-powered tools to interact with external services like Shopify.

### How MCP Helps with Token Management

#### a) Secure Token Storage

MCP servers can act as a secure intermediary for storing and retrieving tokens:

```python
# Conceptual — using MCP to retrieve a stored token
# Instead of reading from .env, the MCP server manages the token vault

# The MCP server (e.g., shopify-dev-mcp) can:
# 1. Store access tokens in an encrypted vault
# 2. Rotate tokens automatically on re-installation
# 3. Inject tokens into API calls without exposing them to the LLM
```

#### b) Reusing Tokens Across Sessions

```
┌───────────────┐     ┌───────────────┐     ┌──────────────┐
│  AI Agent     │────▶│  MCP Server   │────▶│   Shopify    │
│  (Claude, etc)│     │  (Token Vault)│     │   Admin API  │
└───────────────┘     └───────────────┘     └──────────────┘
                            │
                    Stores tokens per shop
                    Handles auth headers
                    Rate-limits requests
```

The MCP server:

- **Stores tokens per-shop** in a database/vault
- **Injects `X-Shopify-Access-Token` headers** automatically
- **Handles API versioning** centrally
- **Rate-limits** requests to avoid throttling

#### c) Multi-Store Management

For multi-store installations, MCP provides a unified interface:

```json
{
    "stores": [
        {
            "shop": "store-a.myshopify.com",
            "token": "shpat_aaa...",
            "scopes": "read_orders,read_fulfillments",
            "installed_at": "2025-01-15T10:30:00Z"
        },
        {
            "shop": "store-b.myshopify.com",
            "token": "shpat_bbb...",
            "scopes": "read_orders,write_orders",
            "installed_at": "2025-02-01T14:00:00Z"
        }
    ]
}
```

The `Shop` model in this project already supports this pattern — each shop's token is stored independently in SQLite.

#### d) Using the Shopify Dev MCP Server

If you have the `shopify-dev-mcp` MCP server configured:

```json
// mcp_config.json
{
    "mcpServers": {
        "shopify-dev-mcp": {
            "command": "npx",
            "args": ["-y", "@anthropic/shopify-dev-mcp@latest"]
        }
    }
}
```

This gives AI agents access to:

- `learn_shopify_api` — Load Shopify API context
- `introspect_graphql_schema` — Explore the Admin GraphQL schema
- `search_docs_chunks` — Search Shopify documentation
- `validate_graphql_codeblocks` — Validate GraphQL queries

---

## 8. Security Best Practices

### ✅ Do

| Practice | Why |
|---|---|
| **Always verify HMAC** on the callback | Prevents forged requests |
| **Always verify the `state` nonce** | Prevents CSRF attacks |
| **Store tokens encrypted at rest** | SQLite is plaintext on disk |
| **Use HTTPS in production** | OAuth tokens in flight must be encrypted |
| **Validate the shop domain** (`*.myshopify.com`) | Prevents open-redirect attacks |
| **Set `timeout` on all `requests` calls** | Prevents hanging connections |
| **Use the latest API version** (`2025-01`) | Ensures access to latest features & security fixes |
| **Never log the full access token** | Logs can be leaked |

### 🔒 Token Encryption Example

```python
# Using cryptography library for at-rest encryption
from cryptography.fernet import Fernet

# Generate a key once, store in env
# ENCRYPTION_KEY = Fernet.generate_key().decode()
ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]
fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
```

### 🔒 Rate Limiting the Install Endpoint

```python
# Using flask-limiter
from flask_limiter import Limiter

limiter = Limiter(key_func=lambda: request.remote_addr)

@auth_bp.route("/install")
@limiter.limit("10 per minute")
def install():
    ...
```

---

## 9. Common Mistakes to Avoid

### ❌ Mistake 1: Using `grant_options[]=per-user`

```python
# WRONG — this generates an ONLINE token (short-lived, tied to user)
params = {
    "client_id": api_key,
    "scope": scopes,
    "redirect_uri": redirect_uri,
    "state": nonce,
    "grant_options[]": "per-user",   # ← REMOVE THIS
}
```

**Fix**: Omit `grant_options[]` entirely. The default is offline access.

---

### ❌ Mistake 2: Not verifying HMAC

```python
# WRONG — skipping HMAC verification
@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")
    shop = request.args.get("shop")
    # Directly exchanging... DANGEROUS!
```

**Fix**: Always verify the HMAC signature before exchanging the code.

---

### ❌ Mistake 3: Hardcoding secrets

```python
# WRONG
api_key = "shpat_abc123"
api_secret = "shpss_xyz789"
```

**Fix**: Always use environment variables via `os.environ` or Flask's `current_app.config`.

---

### ❌ Mistake 4: Not handling token rotation on re-install

When a merchant uninstalls and re-installs your app, Shopify issues a **new** token.
The old token is invalidated.

```python
# CORRECT — upsert pattern
existing_shop = Shop.query.filter_by(shop_url=shop).first()
if existing_shop:
    existing_shop.access_token = access_token  # Update existing
else:
    new_shop = Shop(shop_url=shop, access_token=access_token)
    db.session.add(new_shop)
db.session.commit()
```

---

### ❌ Mistake 5: Using a deprecated API version

```python
# WRONG — 2024-01 is deprecated
url = f"https://{shop}/admin/api/2024-01/orders.json"

# CORRECT — use the latest stable version
url = f"https://{shop}/admin/api/2025-01/orders.json"
```

Check the latest version at: <https://shopify.dev/docs/api/usage/versioning>

---

## Quick Reference

### API Endpoints Used

| Endpoint | Method | Description |
|---|---|---|
| `/admin/oauth/authorize` | `GET` (redirect) | Start OAuth consent |
| `/admin/oauth/access_token` | `POST` | Exchange code for token |
| `/admin/api/2025-01/orders.json` | `GET` | List orders |
| `/admin/api/2025-01/orders/{id}.json` | `GET` | Single order |
| `/admin/api/2025-01/orders/{id}/fulfillments.json` | `GET` | Order fulfillments |

### Required Headers for API Calls

```python
headers = {
    "X-Shopify-Access-Token": "shpat_xxxxxxxxxxxxxxx",
    "Content-Type": "application/json",
}
```

### Flask Routes in This Project

| Route | Purpose |
|---|---|
| `GET /auth/install?shop=xxx.myshopify.com` | Begin OAuth flow |
| `GET /auth/callback` | Handle Shopify redirect, exchange code for token |
| `GET /auth/status?shop=xxx.myshopify.com` | Check if token is stored |
