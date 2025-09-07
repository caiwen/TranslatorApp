# test_google_translate.py

from googletrans import Translator
import time


def test_google_translate():
    # 初始化 Google 翻译器，设置超时时间和备用服务
    translator = Translator(service_urls=['translate.google.com'])

    # 测试文本，包含字符串、数字、空值、None
    test_texts = [
        "你好，世界",
        12345,
        3.14159,
        "",
        None,
        "Python 编程非常有趣"
    ]

    print("开始测试 Google 翻译接口...\n")

    for text in test_texts:
        # 空值处理 + 强制转换为字符串
        text_str = "" if text is None else str(text)
        try:
            result = translator.translate(text_str, dest="en")
            print(f"原文: {text} -> 翻译: {result.text}\n")
        except Exception as e:
            print(f"翻译出错: {e}\n")

        # 控制请求频率，避免被封
        time.sleep(0.5)


if __name__ == "__main__":
    test_google_translate()
