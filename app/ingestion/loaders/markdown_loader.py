from .text_loader import TextLoader
from .base import RawDocument

class MarkdownLoader(TextLoader):
    def load(self, file_content: bytes, filename: str, document_id: str) -> RawDocument:
        doc = super().load(file_content, filename, document_id)
        doc.file_type = "md"
        return doc
