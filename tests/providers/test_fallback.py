import pytest
from app.llm.orchestrator import llm_orchestrator
from app.llm.circuit_breaker import gemini_circuit_breaker

def test_provider_001_primary_or_quota_fallback():
    # Normal query - succeeds via Gemini (if quota active) or immediately via Groq fallback (if quota exhausted)
    res = llm_orchestrator.generate("What is the speed of light?")
    assert res.provider in ["gemini", "groq"]
    if res.provider == "groq":
        assert res.fallback_used is True
        assert res.fallback_reason in ["gemini_quota_exhausted", "circuit_breaker_open", "gemini_exhausted_retries"]
    else:
        assert res.fallback_used is False

def test_provider_002_timeout_falls_back():
    res = llm_orchestrator.generate("trigger_provider_timeout")
    assert res.provider == "groq"
    assert res.fallback_used is True
    assert res.fallback_reason == "gemini_exhausted_retries"

def test_provider_003_gemini_500():
    res = llm_orchestrator.generate("trigger_provider_500")
    assert res.provider == "groq"
    assert res.fallback_used is True

def test_provider_004_429_quota_immediate_fallback_no_retries():
    # Proves: 429 quota error -> immediate classification -> 0 extra retries -> Groq fallback succeeds
    res = llm_orchestrator.generate("trigger_provider_429_quota")
    assert res.provider == "groq"
    assert res.fallback_used is True
    assert res.fallback_reason == "gemini_quota_exhausted"
    assert res.attempts == 1

def test_provider_007_both_fail():
    res = llm_orchestrator.generate("trigger_provider_500 trigger_groq_500")
    assert res.provider == "none"
    assert res.fallback_used is True
    assert res.fallback_reason == "both_providers_failed"
