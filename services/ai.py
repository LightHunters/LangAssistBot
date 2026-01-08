from openai import OpenAI
import config

class AIService:
    def __init__(self):
        self.client = OpenAI(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": config.SITE_URL,
                "X-Title": config.SITE_NAME,
            }
        )

    def get_chat_response(self, user_text: str) -> str:
        response = self.client.chat.completions.create(
            model=config.AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": user_text},
            ],
            stream=False
        )
        return response.choices[0].message.content

ai_service = AIService()
