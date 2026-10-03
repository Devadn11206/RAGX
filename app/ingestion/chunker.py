from typing import List, Dict, Any
from app.core.config import settings

class Chunk:
    def __init__(self, chunk_id: str, document_id: str, chunk_index: int, text: str, page_number: int, filename: str):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.text = text
        self.page_number = page_number
        self.filename = filename

class DocumentChunker:
    def __init__(self):
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP

    def chunk_document(self, raw_document) -> List[Chunk]:
        chunks = []
        chunk_idx = 0
        
        for page in raw_document.pages:
            text = page.text
            # Basic approximation: 1 token ~ 4 chars for English
            char_chunk_size = self.chunk_size * 4
            char_overlap = self.chunk_overlap * 4
            
            start = 0
            while start < len(text):
                end = start + char_chunk_size
                chunk_text = text[start:end]
                
                if chunk_text.strip():
                    chunk_id = f"{raw_document.document_id}_{chunk_idx}"
                    chunks.append(Chunk(
                        chunk_id=chunk_id,
                        document_id=raw_document.document_id,
                        chunk_index=chunk_idx,
                        text=chunk_text.strip(),
                        page_number=page.page_number,
                        filename=raw_document.filename
                    ))
                    chunk_idx += 1
                
                if end >= len(text):
                    break
                    
                start += char_chunk_size - char_overlap
                
        return chunks
