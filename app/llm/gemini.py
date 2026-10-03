import logging
import time
import re
from google import genai
from app.core.config import settings
from .provider import LLMProvider
from .models import (
    LLMResponse, 
    ProviderTimeoutError, 
    ProviderRateLimitError, 
    ProviderQuotaExhaustedError, 
    ProviderAuthenticationError, 
    ProviderInvalidRequestError, 
    ProviderServerError, 
    ProviderError,
    ErrorCategory
)

logger = logging.getLogger(__name__)

class LLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class GeminiClient(LLMProvider):
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options={"api_version": "v1"}
                )
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
        
    def _classify_error(self, err_str: str) -> ProviderError:
        err_lower = err_str.lower()
        
        # Check for retry delay
        retry_delay = None
        match = re.search(r"retrydelay['\":\s]+(\d+)", err_str, re.IGNORECASE)
        if match:
            try:
                retry_delay = float(match.group(1))
            except Exception:
                pass
                
        # 1. Quota Exhaustion vs Short Rate Limit
        if "resource_exhausted" in err_lower or "quota" in err_lower or "quota exceeded" in err_lower:
            return ProviderQuotaExhaustedError(f"Gemini quota exhausted: {err_str}", retry_delay=retry_delay)
        if "429" in err_str:
            if retry_delay and retry_delay > 60:
                return ProviderQuotaExhaustedError(f"Gemini quota exhausted (long retry delay {retry_delay}s): {err_str}", retry_delay=retry_delay)
            return ProviderRateLimitError(f"Gemini rate limit exceeded: {err_str}", retry_delay=retry_delay)
            
        # 2. Timeout
        if "deadline" in err_lower or "timeout" in err_lower or "timed out" in err_lower:
            return ProviderTimeoutError(f"Gemini timeout: {err_str}")
            
        # 3. Auth
        if "401" in err_str or "403" in err_str or "unauthenticated" in err_lower or "permission_denied" in err_lower or "api_key" in err_lower:
            return ProviderAuthenticationError(f"Gemini authentication error: {err_str}")
            
        # 4. Invalid request
        if "400" in err_str or "invalid_argument" in err_lower:
            return ProviderInvalidRequestError(f"Gemini invalid request: {err_str}")
            
        # 5. Server error / Transient
        if "500" in err_str or "503" in err_str or "502" in err_str or "unavailable" in err_lower or "internal" in err_lower:
            return ProviderServerError(f"Gemini server error: {err_str}")
            
        return ProviderError(f"Gemini error: {err_str}", category=ErrorCategory.SERVER_ERROR)

    def generate(self, prompt: str, model_name: str = None) -> LLMResponse:
        start = time.time()
        
        # Test triggers for provider resilience
        if "trigger_provider_timeout" in prompt:
            raise ProviderTimeoutError("Simulated Gemini Timeout")
        if "trigger_provider_500" in prompt:
            raise ProviderServerError("Simulated Gemini 500 Internal Server Error")
        if "trigger_provider_429_quota" in prompt:
            raise ProviderQuotaExhaustedError("Simulated Gemini Quota Exhaustion (429 RESOURCE_EXHAUSTED)", retry_delay=24000.0)
        if "trigger_provider_429_rate" in prompt:
            raise ProviderRateLimitError("Simulated Gemini Rate Limit (429)", retry_delay=2.0)
        if "trigger_provider_auth" in prompt:
            raise ProviderAuthenticationError("Simulated Gemini Auth Failure (401)")

        if not settings.GEMINI_API_KEY or not self.client:
            # Mock mode if no key
            logger.warning("No GEMINI_API_KEY provided or client uninitialized. Returning mock response.")
            ans = "I don't know." if "fail_on_purpose" in prompt else f"This is a mock answer from {model_name or settings.GEMINI_MODEL}."
            latency = int((time.time() - start) * 1000)
            return LLMResponse(
                content=ans,
                provider="gemini",
                model=model_name or settings.GEMINI_MODEL,
                latency_ms=latency,
                estimated_cost=0.0
            )
            
        try:
            import concurrent.futures
            target_model = model_name or settings.GEMINI_MODEL
            
            def _call():
                return self.client.models.generate_content(
                    model=target_model,
                    contents=prompt
                )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call)
                try:
                    response = future.result(timeout=settings.GEMINI_TIMEOUT_SECONDS)
                except concurrent.futures.TimeoutError:
                    raise ProviderTimeoutError(f"Gemini call timed out after {settings.GEMINI_TIMEOUT_SECONDS}s")
                    
            latency = int((time.time() - start) * 1000)
            text_content = response.text if hasattr(response, 'text') and response.text else ""
            
            # Estimate token cost
            input_tokens = len(prompt) // 4
            output_tokens = len(text_content) // 4
            cost = (input_tokens * 0.000000075) + (output_tokens * 0.00000030) # standard Gemini 1.5/2.0 Flash pricing
            
            return LLMResponse(
                content=text_content,
                provider="gemini",
                model=target_model,
                latency_ms=latency,
                estimated_cost=cost
            )
        except (ProviderError,):
            raise
        except Exception as e:
            classified = self._classify_error(str(e))
            logger.error(f"Gemini generation failed [{classified.category}]: {str(e)}")
            raise classified

llm_client = GeminiClient()
