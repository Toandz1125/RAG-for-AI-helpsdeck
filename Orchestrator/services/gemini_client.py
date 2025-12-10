import google.generativeai as genai

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = model

    def generate(self, prompt: str):
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return response.text
