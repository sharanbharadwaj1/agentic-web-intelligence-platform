from groq import Groq
from config.settings import settings

class GroqClient:
    def __init__(self, model_name=None, api_key=None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model_name or settings.GROQ_MODEL
        self.client = Groq(api_key=self.api_key)

    def ask(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Groq Error] {e}"

    def structured(self, prompt: str, schema=None) -> str:
        try:
            messages = []
            if schema:
                messages.append({
                    "role": "system",
                    "content": f"Return ONLY valid JSON matching schema: {schema}"
                })
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Groq Error] {e}"
