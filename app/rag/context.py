from typing import List, Dict, Any

class ContextBuilder:
    @staticmethod
    def build(chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return ""
            
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            page_info = f"\nPage: {chunk['page_number']}" if chunk.get('page_number') is not None else ""
            part = f"[Source {i}]\nDocument: {chunk['filename']}{page_info}\nContent:\n{chunk['text']}"
            context_parts.append(part)
            
        return "\n\n".join(context_parts)
