import pytest
from app.llm.orchestrator import llm_orchestrator
from app.llm.circuit_breaker import gemini_circuit_breaker
import time

def test_provider_008_circuit_breaker():
    # Force 5 failures
    gemini_circuit_breaker.failure_count = 0
    gemini_circuit_breaker.state = "CLOSED"
    gemini_circuit_breaker.cooldown_seconds = 1 # override for test
    
    for _ in range(5):
        # We mock by calling directly to not sleep via orchestrator retry
        gemini_circuit_breaker.record_failure()
        
    assert gemini_circuit_breaker.state == "OPEN"
    
    # Request should skip Gemini now
    res = llm_orchestrator.generate("hello")
    assert res.provider == "groq"
    assert res.fallback_reason == "circuit_breaker_open"
    
    # Wait for cooldown
    time.sleep(1.1)
    
    # Next call should be HALF_OPEN
    assert gemini_circuit_breaker.allow_request() == True
    assert gemini_circuit_breaker.state == "HALF_OPEN"
    
    # Simulate success
    gemini_circuit_breaker.record_success()
    assert gemini_circuit_breaker.state == "CLOSED"
