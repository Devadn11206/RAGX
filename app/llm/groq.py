import time
import logging
from .provider import LLMProvider
from .models import (
    LLMResponse, 
    ProviderTimeoutError, 
    ProviderRateLimitError, 
    ProviderServerError, 
    ProviderAuthenticationError, 
    ProviderInvalidRequestError, 
    ProviderError,
    ErrorCategory
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class GroqClient(LLMProvider):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
            except ImportError:
                raise ProviderError("groq package not installed. Run: pip install groq", category=ErrorCategory.SERVER_ERROR)
        return self._client

    def _classify_error(self, err_str: str) -> ProviderError:
        err_lower = err_str.lower()
        if "timeout" in err_lower or "timed out" in err_lower:
            return ProviderTimeoutError(f"Groq timeout: {err_str}")
        if "rate_limit" in err_lower or "429" in err_str:
            return ProviderRateLimitError(f"Groq rate limit: {err_str}")
        if "401" in err_str or "auth" in err_lower or "api_key" in err_lower:
            return ProviderAuthenticationError(f"Groq auth error: {err_str}")
        if "400" in err_str or "invalid" in err_lower:
            return ProviderInvalidRequestError(f"Groq invalid request: {err_str}")
        if "500" in err_str or "503" in err_str or "internal" in err_lower:
            return ProviderServerError(f"Groq server error: {err_str}")
        return ProviderError(f"Groq error: {err_str}", category=ErrorCategory.SERVER_ERROR)

    def generate(self, prompt: str, model_name: str = None) -> LLMResponse:
        start = time.time()
        
        # Test triggers for provider resilience
        if "trigger_groq_timeout" in prompt:
            raise ProviderTimeoutError("Simulated Groq Timeout")
        if "trigger_groq_500" in prompt:
            raise ProviderServerError("Simulated Groq 500 Internal Server Error")

        if not self.api_key:
            logger.warning("No GROQ_API_KEY provided. Returning mock response.")
            ans = "I don't know." if "fail_on_purpose" in prompt else f"This is a fallback mock answer from Groq {model_name or settings.GROQ_SMALL_MODEL}."
            latency = int((time.time() - start) * 1000)
            return LLMResponse(
                content=ans,
                provider="groq",
                model=model_name or settings.GROQ_SMALL_MODEL,
                latency_ms=latency,
                estimated_cost=0.0
            )
            
        try:
            target_model = model_name or settings.GROQ_SMALL_MODEL
            client = self._get_client()
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=target_model,
                timeout=settings.GROQ_TIMEOUT_SECONDS,
                max_tokens=384, # Safe limit to avoid Groq 1000 OTPM rate limit on free tier
            )
            
            content = chat_completion.choices[0].message.content or ""
            latency = int((time.time() - start) * 1000)
            
            # Accurate token cost calculation
            input_tokens = chat_completion.usage.prompt_tokens if chat_completion.usage else len(prompt) // 4
            output_tokens = chat_completion.usage.completion_tokens if chat_completion.usage else len(content) // 4
            cost = (input_tokens * 0.00000005) + (output_tokens * 0.00000008)
            
            return LLMResponse(
                content=content,
                provider="groq",
                model=target_model,
                latency_ms=latency,
                estimated_cost=cost
            )
        except ProviderError:
            raise
        except Exception as e:
            classified = self._classify_error(str(e))
            logger.error(f"Groq generation failed [{classified.category}]: {str(e)}")
            raise classified

groq_client = GroqClient()
