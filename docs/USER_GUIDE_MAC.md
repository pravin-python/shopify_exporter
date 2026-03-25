# 🍎 Shopify Local Exporter — macOS User Guide

A complete step-by-step guide to set up and use the **Shopify Local Exporter** application on **macOS**.

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Download the Project](#2-download-the-project)
3. [Setup Virtual Environment](#3-setup-virtual-environment)
4. [Install Dependencies](#4-install-dependencies)
5. [Configure Environment Variables](#5-configure-environment-variables)
6. [Initialize the Database](#6-initialize-the-database)
7. [Start the Application](#7-start-the-application)
8. [Using the Application](#8-using-the-application)
9. [Stopping the Server](#9-stopping-the-server)
10. [Daily Usage Quick Reference](#10-daily-usage-quick-reference)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

Before you begin, make sure you have:

- ✅ **Python 3.9 or higher** installed — See `PYTHON_INSTALLATION_GUIDE.md` if not installed
- ✅ **Git** installed — See `GIT_INSTALLATION_GUIDE.md` if not installed
- ✅ **Shopify Store credentials** (Store URL, API Key, API Secret)
- ✅ A text editor (TextEdit, VS Code, nano, etc.)

Open **Terminal** (search "Terminal" in Spotlight or find it in Applications → Utilities) and verify Python:
```bash
python3 --version
```
Output should be `Python 3.9.x` or higher.

> **Important:** On macOS, always use `python3` and `pip3` instead of `python` and `pip`.

Verify Git:
```bash
git --version
```
Output should be `git version 2.x.x` or higher. If not installed, see `GIT_INSTALLATION_GUIDE.md`.

---

## 2. Download the Project

### Option A — Using Git (Recommended)

> 💡 **Git not installed?** See `GIT_INSTALLATION_GUIDE.md` for step-by-step installation instructions.

```bash
git clone https://github.com/pravin-python/shopify_exporter.git
cd shopify_exporter
```

### Option B — Download ZIP (Without Git)

If you don't want to install Git, you can download the project as a ZIP file:

1. Open your browser and go to: **[https://github.com/pravin-python/shopify_exporter](https://github.com/pravin-python/shopify_exporter)**
2. Click the green **"<> Code"** button → Click **"Download ZIP"**.
3. Double-click the downloaded ZIP file to extract it.
4. Move the extracted folder to a convenient location (e.g., your Desktop or Home folder).

> ⚠️ **Note:** With the ZIP method, you won't be able to use `git pull` for future updates. We recommend installing Git for the best experience.

---

## 3. Setup Virtual Environment

A virtual environment keeps this project's libraries separate from your other Python projects.

### Open Terminal in the Project Folder

**Method 1 — Drag & Drop:**
1. Open **Terminal**.
2. Type `cd ` (with a space after it).
3. Drag the `shopify_exporter` folder from Finder into the Terminal window.
4. Press **Enter**.

**Method 2 — Direct navigation:**
```bash
cd ~/Desktop/shopify_exporter
```
(Adjust the path to wherever your project is located.)

### Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

After activation, you will see `(venv)` at the beginning of your terminal prompt:
```
(venv) username@MacBook shopify_exporter %
```

---

## 4. Install Dependencies

With the virtual environment activated, install all required packages:

```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs: Flask, SQLAlchemy, pandas, requests, waitress, python-dotenv.

---

## 5. Configure Environment Variables

### Step 1 — Create the `.env` file

```bash
cp .env.example .env
```

### Step 2 — Edit the `.env` file

Open the file in your preferred text editor:

```bash
# Using nano (built-in terminal editor)
nano .env

# OR using VS Code (if installed)
code .env

# OR using TextEdit
open -a TextEdit .env
```

### Step 3 — Fill in your credentials

Update the following values with your actual Shopify information:

```env
# Flask configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=any-random-secret-string-here

# Shopify configuration
SHOPIFY_STORE=your-store-name.myshopify.com

# Shopify OAuth (from Partner Dashboard → App → API credentials)
SHOPIFY_API_KEY=your-app-api-key
SHOPIFY_API_SECRET=your-app-api-secret-key
SHOPIFY_SCOPES=read_orders,read_fulfillments
SHOPIFY_REDIRECT_URI=http://localhost:5000/auth/callback
```

**Where to find these values:**
- **SHOPIFY_STORE**: Your Shopify store URL (e.g., `my-store.myshopify.com`)
- **SHOPIFY_API_KEY & SHOPIFY_API_SECRET**: Go to [Shopify Partner Dashboard](https://partners.shopify.com/) → Your App → **API credentials**
- **SECRET_KEY**: A secure random string used by Flask to sign session cookies and protect against tampering. You should generate a strong one — **do not use a simple string in production.**

#### 🔑 How to generate a secure SECRET_KEY

Open Terminal and run:
```bash
python3 -c "import secrets; print(secrets.token_hex(24))"
```

This will output a random 48-character hex string, for example:
```
3f8a2c1e9b4d7e6f0a5c2b8d1e4f7a3c9b6d2e5f8a1c4b7
```

Copy that output and paste it as the value for `SECRET_KEY` in your `.env` file:
```env
SECRET_KEY=3f8a2c1e9b4d7e6f0a5c2b8d1e4f7a3c9b6d2e5f8a1c4b7
```

> ⚠️ **Important:** Never share your `SECRET_KEY` with anyone. Never commit your `.env` file to Git.

If using nano: Press **Ctrl + O** to save, then **Ctrl + X** to exit.

---

## 6. Initialize the Database

Run this command **once** to create the SQLite database:

```bash
flask --app run init-db
```

You should see:
```
Database initialized successfully.
```

This creates the file `instance/shopify.db`.

---

## 7. Start the Application

Make sure your virtual environment is activated (you see `(venv)` in the prompt).

### Option A — Flask Development Server (Recommended)

```bash
flask --app run run
```

### Option B — Direct Python Entry

```bash
python3 run.py
```

### Option C — Production Server (Waitress)

```bash
waitress-serve --port=5000 run:app
```

### Access the Application

Open your web browser (Safari, Chrome, Firefox) and go to:

**➡️ [http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

You will see the Shopify Local Exporter dashboard.

---

## 8. Using the Application

### 🔗 Step 1 — Connect Your Shopify Store

1. When you open the dashboard, you will see a **"Connect Shopify"** button (if not already connected).
2. Click it to initiate the OAuth token generation process.
3. Once connected, the dashboard will show a success message with your store name and access scopes.

### 📦 Step 2 — Sync Orders from Shopify

1. On the dashboard, set the **Start Date** and **End Date** for the orders you want to fetch.
2. Click the **"Sync Orders"** button.
3. The application will:
   - Fetch orders from your Shopify store via the API.
   - Store them in the local SQLite database.
   - Automatically start fetching email tracking events in the background.
4. You will see a success message like: `"Successfully synced 50 orders."`

### 📬 Step 3 — Sync Delivery Status (USPS)

1. Click the **"Sync Delivery"** button on the dashboard.
2. This checks USPS tracking for all orders with tracking numbers.
3. Delivery statuses will be updated in the database.

### 🔍 Step 4 — Filter & View Orders

- Use the **Date filters** (Start Date, End Date) and **SKU filter** to narrow down orders.
- The dashboard table shows all synced orders with pagination.
- Columns include: Order Name, SKU, Quantity, Tracking Number, Delivery Status, etc.

### 📥 Step 5 — Export to CSV

- **Export All**: Click **"Export All"** to download all currently filtered orders as a CSV file.
- **Export Selected**: Select specific rows using checkboxes, then click **"Export Selected"** to download only those rows.

The CSV file (`shopify_orders_export.csv`) will be saved to your Downloads folder.

---

## 9. Stopping the Server

To stop the Flask server:
- Press **`Ctrl + C`** in the Terminal where the server is running.

To deactivate the virtual environment:
```bash
deactivate
```

---

## 10. Daily Usage Quick Reference

Once initial setup is done, you **do NOT** need to create the venv or pip install again. Just activate and run:

```bash
# Step 1: Open Terminal and navigate to project folder
cd ~/Desktop/shopify_exporter

# Step 2: Activate virtual environment
source venv/bin/activate

# Step 3: Start the server
flask --app run run

# Step 4: Open browser → http://127.0.0.1:5000/
# Step 5: When done, press Ctrl+C to stop → type 'deactivate'
```

> 💡 **Remember:** You only need to run `pip install -r requirements.txt` and `flask --app run init-db` once during the first-time setup. After that, just activate the venv and start the server.

### 🗑️ Reset Database / Fresh Start

If you want to **delete all synced data** and start fresh (remove all orders, emails, sync logs from the database), run:

```bash
# Step 1: Make sure venv is activated
source venv/bin/activate

# Step 2: Re-initialize the database (this deletes all existing data)
flask --app run init-db
```

This will drop and recreate all tables in `instance/shopify.db`. Your `.env` settings and Shopify connection will remain unchanged — you just need to sync orders again.

> ⚠️ **Warning:** This permanently deletes all order data from the local database. Make sure to export any data you need before running this command.

---

## 11. Troubleshooting

### "python3: command not found"

- Python is not installed. See `PYTHON_INSTALLATION_GUIDE.md`.

### "flask: command not found"

- Your virtual environment is not activated. Run `source venv/bin/activate` first.

### Port 5000 is already in use

- On macOS Monterey and later, **AirPlay Receiver** uses port 5000 by default.
- **Fix Option 1:** Disable AirPlay Receiver:
  - Go to **System Settings** → **General** → **AirDrop & Handoff** → Turn off **AirPlay Receiver**.
- **Fix Option 2:** Use a different port:
  ```bash
  flask --app run run --port 5001
  ```
  Then access at `http://127.0.0.1:5001/`

### Permission denied when installing packages

- Use `pip` inside the virtual environment (it doesn't need `sudo`).
- If you're installing globally, use: `pip3 install --user <package>`

### Database errors

- Delete `instance/shopify.db` and run `flask --app run init-db` again:
  ```bash
  rm instance/shopify.db
  flask --app run init-db
  ```

### Cannot connect to Shopify

- Verify your `.env` credentials are correct.
- Ensure your Shopify API key and secret are from the correct app in your Partner Dashboard.
- Make sure your internet connection is working.
