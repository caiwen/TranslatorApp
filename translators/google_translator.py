from googletrans import Translator
from .base import TranslatorInterface

class GoogleTranslator(TranslatorInterface):
    def __init__(self):
        self.translator = Translator(service_urls=['translate.google.com'])

    def translate(self, text: str, target_lang: str) -> str:
        if not text:
            return ""
        try:
            return self.translator.translate(text, dest=target_lang).text
        except Exception as e:
            print(f"Google 翻译出错: {e}")
            return text
