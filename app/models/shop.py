from datetime import datetime
from app.extensions import db
from app.core.timezone_utils import now_pt

class Shop(db.Model):
    __tablename__ = 'shops'

    id = db.Column(db.Integer, primary_key=True)
    shop_url = db.Column(db.String(255), unique=True, nullable=False, index=True)
    access_token = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now_pt, nullable=False)

    def __repr__(self):
        return f"<Shop {self.shop_url}>"
