import pytest
from app.services.graph_service import graph_service
from app.rag.graph_extractor import graph_extractor

@pytest.mark.asyncio
async def test_graph_extraction_logic():
    text = "Alice founded Acme Corp in 2015. Acme Corp later developed the SuperWidget."
    extraction = graph_extractor.extract(text)
    
    # We gracefully skip tests if API doesn't return (like in CI environment without keys)
    if extraction is None:
        pytest.skip("No LLM key or LLM failed to extract")
        
    assert len(extraction.entities) > 0
    assert len(extraction.relations) > 0
    
    names = [e.name for e in extraction.entities]
    assert any("Alice" in n for n in names)
    assert any("Acme" in n for n in names)
