# Running in Production

To run this application in a production environment on Windows, use the provided `start_server.bat` script.

This uses **Waitress**, a production-quality pure-Python WSGI server, instead of the built-in Flask development server.

## Quick Start

1. **Stop** any running development server.
2. Double-click **`start_server.bat`**.

## Manual Steps

If you prefer to run manually via terminal:

1. Install the production dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2. Start the server using `waitress`:

    ```bash
    waitress-serve --port=8080 run:app
    ```

    *Or run the python script directly:*

    ```bash
    python wsgi.py
    ```

## Access

The server will be available at `http://localhost:8080` (or your machine's IP address on the network).
