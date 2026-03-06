import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class ShopifyClient:

    def __init__(self, store_url: str, access_token: str):
        self.store_url = store_url
        self.access_token = access_token
        self.api_version = "2026-01"

        self.endpoint = f"https://{self.store_url}/admin/api/{self.api_version}/graphql.json"

        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }

    def get_orders_with_tracking(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:

        # Default last 7 days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=250)
        if not end_date:
            end_date = datetime.utcnow()

        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        orders_data = []
        cursor = None
        has_next_page = True

        while has_next_page:

            after_part = f', after: "{cursor}"' if cursor else ""

            query = f"""
            {{
              orders(
                first: 50
                query: "created_at:>={start_iso} created_at:<={end_iso}"
                {after_part}
              ) {{
                edges {{
                  cursor
                  node {{
                    id
                    name
                    createdAt
                    totalPriceSet {{
                        shopMoney {{
                            amount
                            currencyCode
                        }}
                    }}

                    lineItems(first: 250) {{
                        edges {{
                            node {{
                                id
                                title
                                quantity
                                sku
                                variantTitle
                                vendor
                                originalUnitPriceSet {{
                                    shopMoney {{
                                        amount
                                        currencyCode
                                    }}
                                }}
                                totalDiscountSet {{
                                    shopMoney {{
                                        amount
                                        currencyCode
                                    }}
                                }}
                            }}
                        }}
                    }}
                    fulfillments(first: 250) {{
                      createdAt
                      trackingInfo {{
                        number
                        url
                        company
                      }}
                      events(first: 10) {{
                        edges {{
                            node {{
                                status
                                happenedAt
                            }}
                        }}
                      }}
                    }}
                  }}
                }}
                pageInfo {{
                  hasNextPage
                  endCursor
                }}
              }}
            }}
            """

            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json={"query": query},
            )

            if response.status_code != 200:
                raise Exception(f"Shopify API Error: {response.text}")

            data = response.json()
            print(data)
            orders = data["data"]["orders"]["edges"]

            for edge in orders:
                order = edge["node"]
                fulfillments_data = []
                items = []
                for f in (order.get("fulfillments") or []):
                    fulfillments_data.append(f)
                
                for item in order.get("lineItems", {}).get("edges", []):
                    items.append(item["node"])
                    

                orders_data.append({
                    "order_id": order["id"],
                    "order_name": order["name"],
                    "order_created_at": order["createdAt"],
                    "fulfillment": fulfillments_data,
                    "items": items,
                })

            # Pagination control
            page_info = data["data"]["orders"]["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

            # Shopify rate limit safe delay
            time.sleep(0.5)

        return orders_data

    def get_order_shipping_email_event(self, order_gid: str) -> Optional[Dict]:
        """
        Fetch order events and look for 'Shipping confirmation email'
        """
        query = f"""
        {{
          order(id: "{order_gid}") {{
            events(first: 50) {{
              edges {{
                node {{
                  message
                  createdAt
                }}
              }}
            }}
          }}
        }}
        """
        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json={"query": query},
        )
        if response.status_code != 200:
            return None
            
        data = response.json()
        try:
            events = data["data"]["order"]["events"]["edges"]
            for edge in events:
                node = edge["node"]
                message = node.get("message", "").lower()
                if message and "shipping update email" in message:
                    return {
                        "message": message,
                        "createdAt": node.get("createdAt")
                    }
        except (KeyError, TypeError):
            pass
            
        return None

if __name__ == "__main__":
    shopify_client = ShopifyClient("plus-store-dws.myshopify.com", "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")
    orders = shopify_client.get_orders_with_tracking()
    print(orders)
