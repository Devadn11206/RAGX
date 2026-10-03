import re

class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        # Remove excessive whitespace but preserve paragraph structure loosely
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        # Remove common PDF extraction artifacts
        text = text.replace('\x00', '')
        return text.strip()
