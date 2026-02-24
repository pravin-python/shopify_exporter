import time
import random
from datetime import datetime, timedelta

class ShopifyClient:
    """Mock Shopify Client for Bulk Operations."""
    
    def __init__(self, store_url, access_token):
        self.store_url = store_url
        self.access_token = access_token

    def trigger_bulk_orders_export(self):
        """Mock triggering a bulk export of orders."""
        return {"bulk_operation_id": f"gid://shopify/BulkOperation/{random.randint(1000, 9999)}"}

    def check_bulk_operation_status(self, operation_id):
        """Mock checking the status of a bulk export."""
        return {
            "status": "COMPLETED",
            "url": "mock_download_url"
        }

    def download_bulk_data(self, url):
        """Mock downloading and returning JSONL data."""
        now = datetime.utcnow()
        mock_data = []
        for i in range(1, 6):
            order_id = f"gid://shopify/Order/1000{i}"
            order = {
                "id": order_id,
                "name": f"#{1000 + i}",
                "createdAt": (now - timedelta(days=i)).isoformat() + "Z",
                "__parentId": None
            }
            mock_data.append(order)
            
            for j in range(random.randint(1, 4)):
                item = {
                    "id": f"gid://shopify/LineItem/2000{i}{j}",
                    "sku": f"SKU-{random.choice(['PRO', 'BASIC', 'PREM'])}-{random.randint(10, 99)}",
                    "quantity": random.randint(1, 3),
                    "__parentId": order_id
                }
                mock_data.append(item)
                
        return mock_data
