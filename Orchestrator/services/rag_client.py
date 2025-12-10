import requests

class RagClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def retrieve(self, query: str, top_k: int = 1):
        url = f"{self.base_url}/search"
        payload = {"query": query, "top_k": top_k}
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()
