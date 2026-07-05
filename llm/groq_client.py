# llm/groq_client.py
import os
from groq import Groq
from tools.utils.headline_extraction_schema import HEADLINE_EXTRACTION_SCHEMA
from llm.config_loader import Config
from llm.settings import settings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import dotenv
dotenv.load_dotenv()
class GroqClient:
    def __init__(self, model_name=None):
        cfg = Config.load()
        api_key_env = os.getenv("GROQ_API_KEY")
        # print(f"{api_key_env=}, {settings.GROQ_API_KEY=}")
        self.api_key = api_key_env if api_key_env else settings.GROQ_API_KEY
        self.model = model_name or cfg["llm"]["fast_model"]
        self.client = Groq(api_key=self.api_key)

    def structured(self, prompt,schema):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You must return ONLY a valid JSON object matching the schema: {schema}\n"
                        "Do not include markdown, code, or explanations."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        return completion.choices[0].message.content


    