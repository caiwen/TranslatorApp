import openai
from .base import TranslatorInterface

class OpenAITranslator(TranslatorInterface):
    def __init__(self, api_key):
        openai.api_key = api_key

    def translate(self, text: str, target_lang: str) -> str:
        if not text:
            return ""
        prompt = f"请将以下内容翻译成{target_lang}:\n{text}"
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI 翻译出错: {e}")
            return text
