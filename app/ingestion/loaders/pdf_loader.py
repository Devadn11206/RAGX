import fitz
from .base import BaseLoader, RawDocument, ExtractedPage
from app.core.exceptions import RAGXException

class PDFLoader(BaseLoader):
    def load(self, file_content: bytes, filename: str, document_id: str) -> RawDocument:
        pages = []
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                pages.append(ExtractedPage(page_number=page_num + 1, text=text))
            
            if not any(p.text.strip() for p in pages):
                raise RAGXException(code="EMPTY_PDF", message="PDF contains no extractable text", status_code=400)
                
            return RawDocument(
                document_id=document_id,
                filename=filename,
                file_type="pdf",
                pages=pages,
                metadata={}
            )
        except RAGXException:
            raise
        except Exception as e:
            raise RAGXException(code="PDF_EXTRACTION_ERROR", message=f"Failed to extract PDF: {str(e)}", status_code=400)
