import random
from datetime import datetime, timedelta

class USPSClient:
    """Mock USPS tracking client."""
    
    def __init__(self, user_id):
        self.user_id = user_id

    def check_delivery_status(self, tracking_number):
        """Mock tracking lookup."""
        statuses = ["Pending", "In-Transit", "Delivered"]
        
        # Determine pseudo-random status
        # E.g., based on tracking number to keep it consistent mock-wise
        hash_val = sum(ord(c) for c in tracking_number)
        status = statuses[hash_val % len(statuses)]
        
        delivered_at = None
        if status == "Delivered":
            # Mock delivery happening within last 48 hours
            delivered_at = datetime.utcnow() - timedelta(hours=(hash_val % 48))
            
        return {
            "tracking_number": tracking_number,
            "status": status,
            "delivered_at": delivered_at
        }
