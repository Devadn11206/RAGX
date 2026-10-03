import time
import logging
from .models import (
    LLMResponse, 
    ProviderError, 
    ProviderQuotaExhaustedError, 
    ProviderAuthenticationError, 
    ProviderInvalidRequestError,
    ErrorCategory
)
from .gemini import llm_client as gemini_client
from .groq import groq_client
from .circuit_breaker import gemini_circuit_breaker
from app.core.config import settings
from app.telemetry.service import telemetry_service

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    def __init__(self):
        self.gemini = gemini_client
        self.groq = groq_client

    def _get_fallback_model(self, model_name: str) -> str:
        if model_name == settings.ROUTER_SMALL_MODEL:
            return settings.GROQ_SMALL_MODEL
        elif model_name == settings.ROUTER_LARGE_MODEL:
            return settings.GROQ_LARGE_MODEL
        return settings.GROQ_SMALL_MODEL

    def generate(self, prompt: str, model_name: str = None, request_id: str = "unknown", is_test_run: bool = False) -> LLMResponse:
        model = model_name or settings.ROUTER_SMALL_MODEL
        estimated_cost = 0.0001 if model == settings.ROUTER_SMALL_MODEL else 0.001
        
        fallback_reason = None
        
        # 1. Circuit Breaker Check
        if gemini_circuit_breaker.allow_request():
            # Try Gemini
            for attempt in range(settings.GEMINI_MAX_RETRIES):
                t_start = time.time()
                try:
                    response = self.gemini.generate(prompt, model)
                    latency = (time.time() - t_start) * 1000
                    gemini_circuit_breaker.record_success()
                    response.attempts = attempt + 1
                    telemetry_service.log_llm_event(request_id, "gemini", model, "primary", True, "", latency, 
                                                   len(prompt)//4, len(response.content)//4, response.estimated_cost, False, attempt, 
                                                   gemini_circuit_breaker.state, is_test_run)
                    return response
                except ProviderError as e:
                    latency = (time.time() - t_start) * 1000
                    telemetry_service.log_llm_event(request_id, "gemini", model, "primary", False, str(e), latency, 
                                                   len(prompt)//4, 0, 0, False, attempt, 
                                                   gemini_circuit_breaker.state, is_test_run)
                    
                    err_cat = getattr(e, "category", ErrorCategory.SERVER_ERROR)
                    logger.warning(f"Gemini attempt {attempt + 1} failed [{err_cat}]: {str(e)}")
                    gemini_circuit_breaker.record_failure()
                    
                    # NON-RETRYABLE ERROR: Quota Exhaustion / Auth / Invalid Request
                    if isinstance(e, ProviderQuotaExhaustedError) or err_cat == ErrorCategory.QUOTA_EXHAUSTED:
                        logger.warning("Gemini Quota Exhausted (429 RESOURCE_EXHAUSTED). Immediate fallback to Groq without repeated retries.")
                        fallback_reason = "gemini_quota_exhausted"
                        break
                    elif isinstance(e, (ProviderAuthenticationError, ProviderInvalidRequestError)) or err_cat in (ErrorCategory.AUTHENTICATION_ERROR, ErrorCategory.INVALID_REQUEST):
                        logger.warning(f"Gemini non-retryable error [{err_cat}]. Immediate fallback to Groq.")
                        fallback_reason = f"gemini_{err_cat.lower()}"
                        break
                        
                    # Genuinely transient errors -> retry with exponential backoff
                    if attempt < settings.GEMINI_MAX_RETRIES - 1:
                        time.sleep(min(2 ** attempt, 5))
            else:
                if fallback_reason is None:
                    fallback_reason = "gemini_exhausted_retries"
        else:
            logger.warning("Gemini Circuit Breaker OPEN. Falling back to Groq immediately.")
            fallback_reason = "circuit_breaker_open"
            
        # 2. Fallback to Groq
        groq_model = self._get_fallback_model(model)
        for attempt in range(settings.GROQ_MAX_RETRIES):
            t_start = time.time()
            try:
                response = self.groq.generate(prompt, groq_model)
                latency = (time.time() - t_start) * 1000
                response.fallback_used = True
                response.fallback_reason = fallback_reason
                response.attempts = attempt + 1
                telemetry_service.log_llm_event(request_id, "groq", groq_model, "fallback", True, fallback_reason, latency, 
                                               len(prompt)//4, len(response.content)//4, response.estimated_cost, True, attempt, 
                                               gemini_circuit_breaker.state, is_test_run)
                return response
            except ProviderError as e:
                latency = (time.time() - t_start) * 1000
                telemetry_service.log_llm_event(request_id, "groq", groq_model, "fallback", False, str(e), latency, 
                                               len(prompt)//4, 0, 0, True, attempt, 
                                               gemini_circuit_breaker.state, is_test_run)
                logger.warning(f"Groq attempt {attempt + 1} failed: {str(e)}")
                if attempt < settings.GROQ_MAX_RETRIES - 1:
                    time.sleep(min(2 ** attempt, 5))
                    
        # 3. Complete Failure
        logger.error("Both providers failed completely.")
        return LLMResponse(
            content="We're temporarily unable to generate an answer. Please try again.",
            provider="none",
            model="none",
            fallback_used=True,
            fallback_reason="both_providers_failed"
        )

llm_orchestrator = LLMOrchestrator()
