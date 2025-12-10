import requests

class LLMClient:
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str):
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        resp = requests.post(url, json=payload)
        resp.raise_for_status()

        return resp.json()["choices"][0]["message"]["content"]
