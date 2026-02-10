import json
import logging
from openai import OpenAI
import config

logger = logging.getLogger(__name__)

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

    def _extract_text_from_response(self, resp):
        """
        Extract textual content from the OpenAI / OpenRouter response object.
        Attempts a few access patterns to be robust.
        """
        try:
           
            parts = resp.output or resp.get("output", [])
            text = ""
            for part in parts:
                for c in part.get("content", []):
                    if isinstance(c, dict) and c.get("type") == "output_text":
                        text += c.get("text", "")
                    elif isinstance(c, str):
                        text += c
            if text:
                return text.strip()
        except Exception:
            pass

        try:
            return resp.choices[0].message.content.strip()
        except Exception:
            pass

        try:
            return resp.choices[0].text.strip()
        except Exception:
            pass

        
        try:
            return json.dumps(resp)
        except Exception:
            return str(resp)

    def get_chat_response(self, user_text: str) -> str:
        """
        Simple chat endpoint (used by /ai). Synchronous.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_text},
        ]
        resp = self.client.chat.completions.create(
            model=config.AI_MODEL,
            messages=messages,
            temperature=0.6,
            stream=False
        )
        return self._extract_text_from_response(resp)

    def analyze_phrase(self, phrase: str, native: str, learning: str) -> dict:
        """
        For LangAssistBot: return structured JSON with keys:
        translation, definition, example, example_translation
        """
        prompt = f"""
Return ONLY valid JSON. No explanation. Keys:
- translation (short translation into the native language)
- definition (1-2 short sentences in the learning language)
- example (one short sentence in the learning language using the phrase)
- example_translation (the example translated into the native language)

Phrase: "{phrase}"
Native language: {native}
Learning language: {learning}
"""

        messages = [
            {"role": "system", "content": "You are a precise language tutor. Return only JSON."},
            {"role": "user", "content": prompt}
        ]

        resp = self.client.chat.completions.create(
            model=config.AI_MODEL,
            messages=messages,
            temperature=0.15,
            stream=False
        )

        text = self._extract_text_from_response(resp)
     
        try:
            parsed = json.loads(text)
          
            result = {
                "translation": parsed.get("translation", "").strip(),
                "definition": parsed.get("definition", "").strip(),
                "example": parsed.get("example", "").strip(),
                "example_translation": parsed.get("example_translation", "").strip(),
            }
            return result
        except Exception:
        
            logger.warning("AI returned non-JSON for analyze_phrase. Using fallback.")
            return {
                "translation": "",
                "definition": text.strip(),
                "example": "",
                "example_translation": "",
            }


ai_service = AIService()