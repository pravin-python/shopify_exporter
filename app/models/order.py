from datetime import datetime
from app.extensions import db
from app.core.timezone_utils import now_pt

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    shopify_order_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    order_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=now_pt, nullable=False)
    payment_status = db.Column(db.String(50), nullable=True, default="UNKNOWN")
    
    # Relationship to OrderItem
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_name}>"
