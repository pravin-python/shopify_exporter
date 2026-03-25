# 📦 Git Installation Guide — All Platforms

A complete step-by-step guide to install **Git** on **Windows**, **macOS**, and **Linux** so you can clone the Shopify Local Exporter project.

---

## 📋 Table of Contents

1. [What is Git?](#1-what-is-git)
2. [Check if Git is Already Installed](#2-check-if-git-is-already-installed)
3. [Install Git on Windows](#3-install-git-on-windows)
4. [Install Git on macOS](#4-install-git-on-macos)
5. [Install Git on Linux](#5-install-git-on-linux)
6. [Verify Installation](#6-verify-installation)
7. [Clone the Project](#7-clone-the-project)
8. [Download Without Git (Alternative)](#8-download-without-git-alternative)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What is Git?

**Git** is a free, open-source version control system used to download (clone) and manage code projects. You need Git to download the Shopify Local Exporter project from GitHub.

---

## 2. Check if Git is Already Installed

Open your **Terminal** (macOS/Linux) or **Command Prompt / PowerShell** (Windows) and run:

```bash
git --version
```

If you see output like `git version 2.x.x`, Git is already installed — you can skip ahead to [Clone the Project](#7-clone-the-project).

If you see `'git' is not recognized` or `command not found`, follow the installation steps below for your operating system.

---

## 3. Install Git on Windows

### Method 1 — Official Installer (Recommended)

1. Go to the official Git download page:
   **➡️ [https://git-scm.com/download/win](https://git-scm.com/download/win)**

2. The download should start automatically. If not, click on **"Click here to download manually"**.

3. Run the downloaded `.exe` installer.

4. Follow the installation wizard — **use all default settings** (just keep clicking **Next**):
   - ✅ Select Components → Keep defaults
   - ✅ Default editor → Keep "Use Vim" or choose "Use Notepad" if you prefer
   - ✅ Adjusting PATH → Select **"Git from the command line and also from 3rd-party software"** (recommended)
   - ✅ HTTPS transport → Select **"Use the OpenSSL library"**
   - ✅ Line ending conversions → Select **"Checkout Windows-style, commit Unix-style line endings"**
   - ✅ Terminal emulator → Select **"Use MinTTY"**
   - Keep clicking **Next** → Click **Install** → Click **Finish**.

5. **Close and reopen** Command Prompt or PowerShell.

6. Verify the installation:
   ```cmd
   git --version
   ```
   You should see something like: `git version 2.47.1.windows.1`

### Method 2 — Using winget (Windows 10/11)

If you have **winget** (Windows Package Manager), open **PowerShell** and run:

```powershell
winget install --id Git.Git -e --source winget
```

After installation, **close and reopen** PowerShell, then verify:
```powershell
git --version
```

---

## 4. Install Git on macOS

### Method 1 — Xcode Command Line Tools (Easiest)

macOS often prompts you to install Git automatically. Open **Terminal** and run:

```bash
git --version
```

If Git is not installed, macOS will show a popup asking you to install **Xcode Command Line Tools**. Click **Install** and wait for it to finish.

If no popup appears, manually install with:
```bash
xcode-select --install
```

After installation, verify:
```bash
git --version
```

### Method 2 — Using Homebrew

If you have **Homebrew** installed, run:

```bash
brew install git
```

After installation, verify:
```bash
git --version
```

### Method 3 — Official Installer

1. Go to: **➡️ [https://git-scm.com/download/mac](https://git-scm.com/download/mac)**
2. Download and run the installer.
3. Follow the on-screen instructions.
4. Verify:
   ```bash
   git --version
   ```

---

## 5. Install Git on Linux

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install git -y
```

### Fedora

```bash
sudo dnf install git -y
```

### CentOS / RHEL

```bash
sudo yum install git -y
```

### Arch Linux

```bash
sudo pacman -S git
```

### openSUSE

```bash
sudo zypper install git
```

After installation, verify:
```bash
git --version
```

---

## 6. Verify Installation

After installing Git, open a **new** terminal window and run:

```bash
git --version
```

✅ **Expected Output:** `git version 2.x.x` (the exact version number may vary)

If you still see an error, try:
- **Windows:** Close and reopen Command Prompt / PowerShell.
- **macOS/Linux:** Close and reopen Terminal.
- If it still doesn't work, restart your computer and try again.

---

## 7. Clone the Project

Once Git is installed, you can download the project using the following command:

### Windows (Command Prompt / PowerShell)

```cmd
git clone https://github.com/pravin-python/shopify_exporter.git
cd shopify_exporter
```

### macOS / Linux (Terminal)

```bash
git clone https://github.com/pravin-python/shopify_exporter.git
cd shopify_exporter
```

This will create a `shopify_exporter` folder with all the project files.

> 💡 **Tip:** You can clone the project to any location. Just navigate to the desired folder first using `cd`, then run the `git clone` command.

---

## 8. Download Without Git (Alternative)

If you **do not want to install Git**, you can download the project manually from GitHub:

### Method 1 — Download ZIP from GitHub

1. Open your web browser and go to:
   **➡️ [https://github.com/pravin-python/shopify_exporter](https://github.com/pravin-python/shopify_exporter)**

2. Click the green **"<> Code"** button.

3. Click **"Download ZIP"**.

4. Extract the downloaded ZIP file:
   - **Windows:** Right-click the ZIP file → **Extract All** → Choose a location.
   - **macOS:** Double-click the ZIP file to extract.
   - **Linux:** Run `unzip shopify_exporter-main.zip`

5. Rename the extracted folder from `shopify_exporter-main` to `shopify_exporter` (optional, for consistency).

> ⚠️ **Note:** When you download as ZIP, you won't be able to use `git pull` to get future updates. You will need to download the ZIP again for any new updates. We recommend installing Git for the best experience.

---

## 9. Troubleshooting

### "'git' is not recognized" (Windows)

- Git is not in your system PATH.
- **Fix 1:** Close and reopen Command Prompt / PowerShell after installation.
- **Fix 2:** Restart your computer.
- **Fix 3:** Reinstall Git and make sure to select **"Git from the command line and also from 3rd-party software"** during installation.

### "git: command not found" (macOS/Linux)

- Git is not installed. Follow the installation steps for your OS above.
- On macOS, try running: `xcode-select --install`

### "Permission denied" when cloning

- Make sure you have internet access.
- Try using HTTPS instead of SSH:
  ```bash
  git clone https://github.com/pravin-python/shopify_exporter.git
  ```

### "fatal: destination path already exists"

- The `shopify_exporter` folder already exists. Either:
  - Delete the existing folder and clone again, OR
  - Clone to a different location:
    ```bash
    git clone https://github.com/pravin-python/shopify_exporter.git shopify_exporter_new
    ```

### SSL certificate problem

- If you see SSL errors behind a corporate firewall:
  ```bash
  git config --global http.sslVerify false
  ```
  > ⚠️ Only use this temporarily. Re-enable SSL verification when not behind the firewall.

### Slow download / timeout

- Check your internet connection.
- Try downloading the ZIP file instead (see [Download Without Git](#8-download-without-git-alternative)).

---

> 💡 **Need more help?** Visit the official Git documentation at [https://git-scm.com/doc](https://git-scm.com/doc)
