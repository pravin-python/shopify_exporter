from run import app
from waitress import serve

if __name__ == "__main__":
    # Serve the application on all interfaces on port 8080
    print("Starting production server on http://0.0.0.0:8080")
    serve(app, host="0.0.0.0", port=8080, threads=6)
