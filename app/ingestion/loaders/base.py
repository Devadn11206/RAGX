from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ExtractedPage(BaseModel):
    page_number: int
    text: str

class RawDocument(BaseModel):
    document_id: str
    filename: str
    file_type: str
    pages: List[ExtractedPage]
    metadata: Dict[str, Any]

class BaseLoader(ABC):
    @abstractmethod
    def load(self, file_content: bytes, filename: str, document_id: str) -> RawDocument:
        pass
