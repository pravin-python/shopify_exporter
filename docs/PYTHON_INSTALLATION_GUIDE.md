# 🐍 Python Installation Guide (Windows / Linux / macOS)

This guide will help you install **Python 3.9 or higher** on your computer. Python is **required** before you can run the Shopify Local Exporter application.

---

## 📋 Table of Contents

1. [Check If Python Is Already Installed](#1-check-if-python-is-already-installed)
2. [Install Python on Windows](#2-install-python-on-windows)
3. [Install Python on macOS](#3-install-python-on-macos)
4. [Install Python on Linux](#4-install-python-on-linux)
5. [Verify Installation](#5-verify-installation)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Check If Python Is Already Installed

Open a terminal / command prompt and type:

```bash
python --version
```
or
```bash
python3 --version
```

If you see something like **`Python 3.9.x`** or higher, Python is already installed and you can skip to the [User Guide for your OS](#next-steps).

If you see `command not found` or a version **lower than 3.9**, follow the installation steps below for your operating system.

---

## 2. Install Python on Windows

### Step 1 — Download Python

1. Open your web browser and go to the official Python website:
   **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
2. Click the big yellow **"Download Python 3.x.x"** button (latest stable version).
3. The `.exe` installer file will start downloading.

### Step 2 — Run the Installer

1. Double-click the downloaded `.exe` file to start the installer.
2. **⚠️ IMPORTANT:** On the first screen, check the box that says:
   > ✅ **"Add python.exe to PATH"**
   
   This is the most important step! Without this, `python` commands won't work from the command prompt.
3. Click **"Install Now"** (recommended) or choose **"Customize installation"** if you need advanced options.
4. Wait for the installation to complete.
5. Click **"Close"** when done.

### Step 3 — Verify

Open **Command Prompt** (search for `cmd` in Start Menu) and type:

```cmd
python --version
```

You should see:
```
Python 3.x.x
```

Also verify `pip` (Python's package manager):
```cmd
pip --version
```

---

## 3. Install Python on macOS

### Option A — Using the Official Installer (Recommended for Beginners)

1. Go to **[https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/)**
2. Download the latest **macOS 64-bit universal2 installer** (`.pkg` file).
3. Double-click the `.pkg` file and follow the installation wizard.
4. Click **Continue** → **Agree** → **Install** → Enter your password → **Close**.

### Option B — Using Homebrew (Recommended for Developers)

If you have [Homebrew](https://brew.sh) installed, run:

```bash
brew install python
```

### Verify

Open **Terminal** (search "Terminal" in Spotlight or look in Applications → Utilities) and run:

```bash
python3 --version
```

You should see:
```
Python 3.x.x
```

Also verify `pip`:
```bash
pip3 --version
```

> **Note:** On macOS, use `python3` and `pip3` instead of `python` and `pip`.

---

## 4. Install Python on Linux

Python is often pre-installed on Linux distributions. Check first:

```bash
python3 --version
```

If it's not installed or is below version 3.9, follow the steps for your distribution:

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

### Fedora

```bash
sudo dnf install python3 python3-pip -y
```

### CentOS / RHEL

```bash
sudo yum install python3 python3-pip -y
```

### Arch Linux

```bash
sudo pacman -S python python-pip
```

### Verify

```bash
python3 --version
pip3 --version
```

---

## 5. Verify Installation

After installation on any platform, open your terminal / command prompt and run these commands:

| Command | Expected Output |
|---------|----------------|
| `python --version` or `python3 --version` | `Python 3.9.x` or higher |
| `pip --version` or `pip3 --version` | `pip 2x.x.x from ...` |

If both commands work, **you're ready to proceed!** 🎉

---

## 6. Troubleshooting

### "python" is not recognized (Windows)

- You probably forgot to check **"Add python.exe to PATH"** during installation.
- **Fix:** Reinstall Python and make sure to check that option, OR manually add Python to your system PATH:
  1. Search **"Environment Variables"** in the Start Menu.
  2. Click **"Edit the system environment variables"**.
  3. Click **"Environment Variables"** button.
  4. Under **"System variables"**, find **Path** → Edit → Add the Python installation path (e.g., `C:\Users\YourName\AppData\Local\Programs\Python\Python3x\`).

### macOS shows old Python 2.x

- macOS sometimes ships with Python 2. Always use `python3` and `pip3` commands.

### Permission denied (Linux)

- Use `sudo` before commands, or install via your package manager.

### pip not found

- Install pip separately:
  ```bash
  python3 -m ensurepip --upgrade
  ```

---

## Next Steps

Once Python is installed successfully, follow the User Guide for your operating system:

- 🪟 **Windows Users** → Read `USER_GUIDE_WINDOWS.md`
- 🍎 **macOS Users** → Read `USER_GUIDE_MAC.md`
- 🐧 **Linux Users** → Read `USER_GUIDE_LINUX.md`

All user guide files are located in the `docs/` folder of this project.
