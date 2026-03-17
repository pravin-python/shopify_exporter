from app.extensions import db

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    sku = db.Column(db.String(100), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Delivery/Fulfillment Status
    fulfilled_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    tracking_url = db.Column(db.String(500), nullable=True)
    tracking_company = db.Column(db.String(100), nullable=True)
    delivery_status = db.Column(db.String(50), nullable=True)
    shipping_email_message = db.Column(db.Text, nullable=True)
    shipping_email_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<OrderItem {self.sku} for Order {self.order_id}>"
