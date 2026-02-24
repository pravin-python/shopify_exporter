from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy extension
# We initialize it here to avoid circular imports between the app factory, models, and blueprints.
db = SQLAlchemy()
