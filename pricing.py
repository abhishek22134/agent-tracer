# Standard pricing per 1 million tokens (USD)
PRICING_TABLE = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "claude-3-5-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "gpt-3.5-turbo": {"input": 0.50 / 1_000_000, "output": 1.50 / 1_000_000},
    "local-ollama": {"input": 0.0, "output": 0.0},
}


def calculate_cost(
    model_name: str, tokens_in: int, tokens_out: int
) -> float:
    """Calculates exact execution cost in USD based on model and token count."""
    rates = PRICING_TABLE.get(
        model_name, {"input": 0.0, "output": 0.0}
    )
    cost = (tokens_in * rates["input"]) + (tokens_out * rates["output"])
    return round(cost, 6)