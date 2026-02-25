# Shopify Local Exporter

A lightweight, local internal Flask application to fetch Shopify orders via Bulk Operations, store them in a local SQLite database, sync delivery statuses from USPS, and export filtered data to CSV.

## Features

- **Local Internal Tool**: Built with Flask and SQLite, not meant for public internet SaaS access.
- **Shopify Sync**: Uses a mock `ShopifyClient` (ready for GraphQL/REST implementations) to pull orders.
- **USPS Sync**: Uses a mock `USPSClient` to verify delivery statuses based on tracking numbers.
- **Date & SKU Filtering**: Easily filter down the raw datasets and view them on a paginated dashboard.
- **CSV Export**: Instantly export matching dashboard records to a clean CSV.

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.9+
- `pip` package manager

### 1. Setup Virtual Environment

It is recommended to run this project in an isolated Python environment.

Open your PowerShell/Terminal in the project directory (`shopify_exporter`):

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Mac/Linux)
source venv/bin/activate
```

### 2. Install Dependencies

Install required libraries from `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Setup Configuration

Create your local environment file:

1. Copy `.env.example` to a new file named `.env`.
2. Open `.env` and fill out the mock values with your actual credentials if ready, or leave as-is for mock testing.

```bash
# Example .env copy command (Windows PowerShell)
Copy-Item .env.example .env

# Example .env copy command (Mac/Linux)
cp .env.example .env
```

### 4. Database Setup & Migration

This project uses SQLAlchemy and an SQLite database located inside the `instance/` folder.

To create the tables for the first time, run the custom CLI command:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
flask --app run init-db
```

*Note: You only need to run this command once to initialize `instance/shopify.db`.*

### 5. Run the Application

Start the Flask development server:

```bash
flask --app run run
```

Or you can simply run the Python entry point:

```bash
python run.py
```

Or run the server using `waitress`:

```bash
waitress-serve --port=8080 run:app
```

Or run the python script directly:

```bash
python wsgi.py
```

The server will start on port 5000. Open your browser and navigate to:
**[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

---

## Project Structure Explained

```text
shopify_exporter/
├── app/                        # Main Flask Application package
│   ├── core/                   # Utilities, Parsers, and Mock API Clients
│   ├── models/                 # SQLAlchemy DB Models (Order, OrderItem)
│   ├── routes/                 # Flask Blueprints for web endpoints
│   ├── static/                 # Custom CSS / JS assets
│   └── templates/              # HTML Jinja2 templates (dashboard)
├── instance/                   # Auto-generated SQLite database goes here
├── venv/                       # Auto-generated Python environment
├── .env.example                # Example environment configuration
├── config.py                   # Central Config object loader
├── requirements.txt            # Python dependencies
└── run.py                      # Server and CLI Command entry point
```

## How to implement Real API Integrations

To switch from the simulated mock environment to real production queries:

1. Open `app/core/shopify_client.py` and replace the JSON dummy logic with an actual `requests.post()` using your `self.access_token` pointing at `admin/api/202x-xx/graphql.json`.
2. Open `app/core/usps_client.py` and connect `requests.get()` to the USPS Tracking API using your `self.user_id`.
