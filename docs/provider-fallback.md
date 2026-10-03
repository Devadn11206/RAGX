# Provider Fallback & Resilience Architecture

This document describes the Phase 7 Provider Resilience layer added to the RAGX platform.

## Overview
The platform uses **Google Gemini** as its primary LLM provider and **Groq** as its fallback provider. The `LLMOrchestrator` intelligently handles transient network errors, timeouts, and rate limits by retrying Gemini with exponential backoff and eventually falling back to Groq if the failure is persistent.

## Features
- **Bounded Retry**: Gemini transient failures are retried up to `GEMINI_MAX_RETRIES` (default: 2) with exponential backoff.
- **Circuit Breaker**: If Gemini fails 5 times consecutively, the circuit opens, and all requests immediately route to Groq for `CIRCUIT_OPEN_SECONDS` (default: 60s). After cooldown, it enters `HALF_OPEN` to test Gemini's health.
- **Quality Escalation Compatibility**: Fallbacks preserve the Phase 6 tier decision. If a fallback small model produces a poor answer, it will still escalate to a large model.
- **Tenant Isolation**: Fallback queries receive the exact same ACL-filtered contexts. Groq does not query external sources.
- **Cost Tracking**: All attempts across all providers are tracked and summed.

## Configuration
Controlled via Environment Variables (`app/core/config.py`):
```text
GROQ_API_KEY=""
GEMINI_TIMEOUT_SECONDS=30
GROQ_TIMEOUT_SECONDS=30
GEMINI_MAX_RETRIES=2
GROQ_MAX_RETRIES=1
CIRCUIT_FAILURE_THRESHOLD=5
CIRCUIT_OPEN_SECONDS=60
CIRCUIT_HALF_OPEN_REQUESTS=1
```

## Failure Classification
- `ProviderTimeoutError`: API timed out.
- `ProviderRateLimitError`: 429 Rate Limit.
- `ProviderError`: Catch-all for 5xx and structural failure.

If both providers fail, a safe error is returned to the user without exposing stack traces or API keys.
