import pytest
from app.ingestion.loaders.text_loader import TextLoader
from app.ingestion.loaders.markdown_loader import MarkdownLoader
from app.ingestion.cleaner import TextCleaner
from app.ingestion.chunker import DocumentChunker
from app.core.exceptions import RAGXException

def test_text_loader():
    loader = TextLoader()
    doc = loader.load(b"Hello world", "test.txt", "doc_1")
    assert doc.file_type == "txt"
    assert len(doc.pages) == 1
    assert doc.pages[0].text == "Hello world"

def test_markdown_loader():
    loader = MarkdownLoader()
    doc = loader.load(b"# Hello", "test.md", "doc_2")
    assert doc.file_type == "md"
    assert doc.pages[0].text == "# Hello"

def test_text_cleaner():
    raw = "Hello   world\n\n\n\nTesting"
    clean = TextCleaner.clean(raw)
    assert clean == "Hello world\n\nTesting"

def test_chunker():
    loader = TextLoader()
    # A chunk is roughly 500 tokens * 4 chars = 2000 chars.
    # Let's override chunker settings for test
    from app.core.config import settings
    old_size = settings.RAG_CHUNK_SIZE
    old_overlap = settings.RAG_CHUNK_OVERLAP
    settings.RAG_CHUNK_SIZE = 10
    settings.RAG_CHUNK_OVERLAP = 2
    
    chunker = DocumentChunker()
    # 40 chars -> chunk size = 10 tokens ~ 40 chars. 
    # overlap = 2 tokens ~ 8 chars
    text = "A" * 100
    doc = loader.load(text.encode(), "test.txt", "doc_3")
    
    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1
    assert chunks[0].text == "A" * 40
    
    settings.RAG_CHUNK_SIZE = old_size
    settings.RAG_CHUNK_OVERLAP = old_overlap
