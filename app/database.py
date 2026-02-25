from app.extensions import db

def init_db():
    """Create database tables."""
    # Import models locally to ensure they are registered with SQLAlchemy
    import app.models.order
    import app.models.order_item
    import app.models.shop
    
    db.create_all()
