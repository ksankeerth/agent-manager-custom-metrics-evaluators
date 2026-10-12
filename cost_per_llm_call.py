import json

from amp_evaluation import EvalResult, Param
from amp_evaluation.trace.models import LLMSpan

# PoC only. Prices are USD per 1M tokens and are EXAMPLES; replace them with your contract prices.
DEFAULT_PRICING = json.dumps({
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
})


def _price(pricing, model):
    if model in pricing:
        return pricing[model]
    for name, price in pricing.items():
        if model.startswith(name):
            return price
    return None


def evaluate(
    llm_span: LLMSpan,
    pricing_json: str = Param(default=DEFAULT_PRICING, description="JSON map: model -> {input, cached_input, output} USD per 1M tokens"),
    max_cost_usd: float = Param(default=0.0005, description="Cost per LLM call that still scores 1.0", min=0),
    cached_included_in_input: bool = Param(default=True, description="True if input tokens already include cached tokens (OpenAI style)"),
) -> EvalResult:
    price = _price(json.loads(pricing_json), llm_span.model or "")
    if price is None:
        return EvalResult.skip(f"No price for model: {llm_span.model or 'unknown'}")
    usage = llm_span.metrics.token_usage
    cached = usage.cache_read_tokens
    fresh = usage.input_tokens - cached if cached_included_in_input else usage.input_tokens
    cost = (fresh * price["input"] + cached * price.get("cached_input", price["input"]) + usage.output_tokens * price["output"]) / 1_000_000
    score = 1.0 if cost <= max_cost_usd else max(0.0, max_cost_usd / cost)
    return EvalResult(
        score=score,
        passed=cost <= max_cost_usd,
        explanation=(f"model={llm_span.model} cost_usd={cost:.6f} input={usage.input_tokens} cached={cached} "
                     f"output={usage.output_tokens} (budget {max_cost_usd})"),
    )
