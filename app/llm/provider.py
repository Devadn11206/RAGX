from .models import LLMResponse

class LLMProvider:
    def generate(self, prompt: str, model_name: str) -> LLMResponse:
        raise NotImplementedError
