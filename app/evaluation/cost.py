from typing import Optional

# Current Gemini 1.5 Pro pricing (approximate example)
PRICING = {
    "gemini-1.5-pro": {
        "input_per_1m": 3.50,
        "output_per_1m": 10.50
    }
}

def calculate_cost(model: str, input_tokens: Optional[int], output_tokens: Optional[int]) -> Optional[float]:
    if input_tokens is None or output_tokens is None:
        return None
    if model not in PRICING:
        return None
        
    prices = PRICING[model]
    cost = (input_tokens / 1_000_000 * prices["input_per_1m"]) + (output_tokens / 1_000_000 * prices["output_per_1m"])
    return round(cost, 6)
