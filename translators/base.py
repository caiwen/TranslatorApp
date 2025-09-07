class TranslatorInterface:
    def translate(self, text: str, target_lang: str) -> str:
        """将 text 翻译为 target_lang，返回翻译结果"""
        raise NotImplementedError
