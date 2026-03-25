# 🐧 Shopify Local Exporter — Linux User Guide

A complete step-by-step guide to set up and use the **Shopify Local Exporter** application on **Linux** (Ubuntu, Debian, Fedora, CentOS, Arch, etc.).

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
- ✅ **pip** and **python3-venv** installed
- ✅ **Shopify Store credentials** (Store URL, API Key, API Secret)
- ✅ A text editor (nano, vim, VS Code, etc.)

Open your **Terminal** and verify Python:
```bash
python3 --version
```
Output should be `Python 3.9.x` or higher.

Verify Git:
```bash
git --version
```
Output should be `git version 2.x.x` or higher. If not installed, see `GIT_INSTALLATION_GUIDE.md`.

If `python3-venv` is not installed (needed for virtual environments):
```bash
# Ubuntu / Debian
sudo apt install python3-venv -y

# Fedora
sudo dnf install python3-virtualenv -y
```

---

## 2. Download the Project

### Option A — Using Git (Recommended)

> 💡 **Git not installed?** See `GIT_INSTALLATION_GUIDE.md` for step-by-step installation instructions.

```bash
git clone https://github.com/pravin-python/shopify_exporter.git
cd shopify_exporter
```

### Option B — Download ZIP / tar.gz (Without Git)

If you don't want to install Git, you can download the project manually:

1. Open your browser and go to: **[https://github.com/pravin-python/shopify_exporter](https://github.com/pravin-python/shopify_exporter)**
2. Click the green **"<> Code"** button → Click **"Download ZIP"**.
3. Extract the downloaded file:

```bash
# For ZIP files
unzip shopify_exporter-main.zip
cd shopify_exporter-main

# For tar.gz files
tar -xzf shopify_exporter.tar.gz
cd shopify_exporter
```

> ⚠️ **Note:** With the ZIP method, you won't be able to use `git pull` for future updates. We recommend installing Git for the best experience.

---

## 3. Setup Virtual Environment

A virtual environment keeps this project's libraries separate from your system Python packages.

### Navigate to the Project Folder

```bash
cd /path/to/shopify_exporter
```
(Replace `/path/to/` with your actual project location.)

### Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

After activation, you will see `(venv)` at the beginning of your terminal prompt:
```
(venv) user@linux:~/shopify_exporter$
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
# Using nano
nano .env

# OR using vim
vim .env

# OR using VS Code (if installed)
code .env
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

#### 🔑 (Optional) How to generate a secure SECRET_KEY
> 💡 **Note:** Generating a custom key is highly recommended for **Production/Deployment**. For local usage, the default value in `.env` is usually sufficient.

Run this command in your Terminal:
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

> ⚠️ **Security Tip:** Never share your `SECRET_KEY` with anyone. Never commit your `.env` file to Git.

If using nano: Press **Ctrl + O** then **Enter** to save, then **Ctrl + X** to exit.

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

### Option D — Run in Background (Advanced)

If you want the server to keep running even after closing the terminal:

```bash
nohup flask --app run run > server.log 2>&1 &
```

To stop a backgrounded server:
```bash
# Find the process
ps aux | grep flask

# Kill it using the PID
kill <PID>
```

### Access the Application

Open your web browser (Firefox, Chrome, etc.) and go to:

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
cd /path/to/shopify_exporter

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
- Try: `sudo apt install python3` (Ubuntu/Debian) or `sudo dnf install python3` (Fedora).

### "flask: command not found"

- Your virtual environment is not activated. Run `source venv/bin/activate` first.

### "ensurepip is not available" or venv creation fails

- Install the `python3-venv` package:
  ```bash
  sudo apt install python3-venv -y    # Ubuntu/Debian
  sudo dnf install python3-virtualenv -y  # Fedora
  ```

### Port 5000 is already in use

- Check what's using the port:
  ```bash
  sudo lsof -i :5000
  ```
- Kill the process or use a different port:
  ```bash
  flask --app run run --port 5001
  ```
  Then access at `http://127.0.0.1:5001/`

### Permission denied errors

- Never use `sudo` with `pip` inside a virtual environment.
- If you need system-wide installation, use: `pip3 install --user <package>`

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
- Test connectivity: `curl -I https://your-store.myshopify.com`

### Firewall blocking port 5000

- Allow the port through the firewall:
  ```bash
  # Ubuntu (UFW)
  sudo ufw allow 5000

  # CentOS/RHEL (firewalld)
  sudo firewall-cmd --add-port=5000/tcp --permanent
  sudo firewall-cmd --reload
  ```
