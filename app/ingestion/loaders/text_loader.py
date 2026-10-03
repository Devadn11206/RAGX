from .base import BaseLoader, RawDocument, ExtractedPage
from app.core.exceptions import RAGXException

class TextLoader(BaseLoader):
    def load(self, file_content: bytes, filename: str, document_id: str) -> RawDocument:
        try:
            text = file_content.decode("utf-8")
            if not text.strip():
                raise RAGXException(code="EMPTY_TEXT", message="Text file is empty", status_code=400)
            
            return RawDocument(
                document_id=document_id,
                filename=filename,
                file_type="txt",
                pages=[ExtractedPage(page_number=1, text=text)],
                metadata={}
            )
        except UnicodeDecodeError:
            raise RAGXException(code="TEXT_DECODE_ERROR", message="Failed to decode text file. Ensure it is UTF-8.", status_code=400)
        except RAGXException:
            raise
