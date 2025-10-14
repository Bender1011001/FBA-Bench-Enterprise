"""
A central registry for the cost-per-million-tokens for various LLM models.
Prices are for input (prompt) tokens and output (completion) tokens.
NOTE: These prices are illustrative and should be updated with the latest figures.
"""

MODEL_PRICING = {
    # OpenAI Models (USD per 1M tokens)
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Anthropic Models (USD per 1M tokens)
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3.5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    # xAI Models (via OpenRouter)
    "xai/grok-1.5-flash": {"input": 0.24, "output": 0.48},
    # Default for unknown models to avoid errors
    "default": {"input": 1.00, "output": 1.00},
}


def get_model_pricing(model_name: str) -> dict:
    """
    Retrieves the pricing for a given model, falling back to a default if not found.
    """
    return MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
