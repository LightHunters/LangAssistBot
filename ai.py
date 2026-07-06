import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_provider():
    return os.getenv("AI_PROVIDER", "openai").strip().lower()


def get_model(provider: str):
    model = os.getenv("AI_MODEL", "").strip()

    if model:
        if provider == "openai" and model.startswith("openai/"):
            return model.split("/", 1)[1]
        return model

    if provider == "openrouter":
        return "openai/gpt-4o-mini"

    return "gpt-4o-mini"


def get_client():
    provider = get_provider()

    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

        if not api_key:
            raise RuntimeError("Missing OPENROUTER_API_KEY in .env")

        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")

    return OpenAI(api_key=api_key)


def extract_json(text: str):
    text = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)

    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI response did not contain valid JSON")

    return json.loads(text[start:end + 1])


def clean_value(value, fallback=""):
    if value is None:
        return fallback

    value = str(value).strip()

    if not value:
        return fallback

    return value


def build_learning_card(phrase: str, native_lang: str, target_lang: str):
    provider = get_provider()
    client = get_client()
    model = get_model(provider)

    system_prompt = """
You are LangAssistBot, a friendly personal language tutor.
You help learners understand unfamiliar words and phrases.
You must return only valid JSON.
"""

    user_prompt = f"""
Native language: {native_lang}
Target language: {target_lang}
Submitted word or phrase: {phrase}

Return only valid JSON with exactly these keys:
phrase
translation
definition
pronunciation
part_of_speech
difficulty
example_target
example_native

Rules:
- Keep the explanation simple.
- Use practical daily language.
- The example_target must be in the target language.
- The example_native must be translated into the native language.
- pronunciation must be text-based.
- difficulty must be one of: beginner, intermediate, advanced.
- If the phrase has multiple meanings, choose the most common meaning.
- Do not include markdown.
- Do not include extra text outside JSON.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0.4,
    )

    content = response.choices[0].message.content
    data = extract_json(content)

    difficulty = clean_value(data.get("difficulty"), "beginner").lower()

    if difficulty not in {"beginner", "intermediate", "advanced"}:
        difficulty = "beginner"

    return {
        "phrase": clean_value(data.get("phrase"), phrase),
        "translation": clean_value(data.get("translation")),
        "definition": clean_value(data.get("definition")),
        "pronunciation": clean_value(data.get("pronunciation")),
        "part_of_speech": clean_value(data.get("part_of_speech")),
        "difficulty": difficulty,
        "example_target": clean_value(data.get("example_target")),
        "example_native": clean_value(data.get("example_native")),
    }