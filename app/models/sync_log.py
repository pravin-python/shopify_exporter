from app.extensions import db
from datetime import datetime
from app.core.timezone_utils import now_pt

class SyncLog(db.Model):
    __tablename__ = 'sync_logs'

    id = db.Column(db.Integer, primary_key=True)
    sync_start_date = db.Column(db.DateTime, nullable=False)
    sync_end_date = db.Column(db.DateTime, nullable=False)
    orders_synced = db.Column(db.Integer, default=0)
    synced_at = db.Column(db.DateTime, default=now_pt)

    def __repr__(self):
        return f"<SyncLog {self.sync_start_date} to {self.sync_end_date}>"
