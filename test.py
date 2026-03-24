import requests
endpoint = "https://plus-store-dws.myshopify.com/admin/api/2026-01/graphql.json"
headers = {"X-Shopify-Access-Token": "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", "Content-Type": "application/json"}
query = """
{
  orders(first: 3) {
    edges {
      node {
        id
        name
        displayFinancialStatus
        createdAt
      }
    }
  }
}
"""
r = requests.post(endpoint, headers=headers, json={"query": query})
import json
print(json.dumps(r.json(), indent=2))
