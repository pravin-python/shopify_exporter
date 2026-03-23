from app import create_app
from app.database import init_db

app = create_app()

@app.cli.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    print("Database initialized successfully.")

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
