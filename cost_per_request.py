import json

from amp_evaluation import EvalResult, Param
from amp_evaluation.trace.models import Trace

# PoC only. Prices are USD per 1M tokens and are EXAMPLES; replace them with your contract prices.
DEFAULT_PRICING = json.dumps({
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
})


def _price(pricing, model):
    if model in pricing:
        return pricing[model]
    for name, price in pricing.items():  # tolerate version suffixes such as gpt-4o-mini-2024-07-18
        if model.startswith(name):
            return price
    return None


def evaluate(
    trace: Trace,
    pricing_json: str = Param(default=DEFAULT_PRICING, description="JSON map: model -> {input, cached_input, output} USD per 1M tokens"),
    max_cost_usd: float = Param(default=0.001, description="Cost per request that still scores 1.0", min=0),
    cached_included_in_input: bool = Param(default=True, description="True if input tokens already include cached tokens (OpenAI style)"),
) -> EvalResult:
    pricing = json.loads(pricing_json)
    calls = trace.get_llm_calls()
    if not calls:
        return EvalResult.skip("No LLM calls in this trace")
    total, cached_total, unpriced = 0.0, 0, []
    for call in calls:
        usage = call.metrics.token_usage
        price = _price(pricing, call.model or "")
        if price is None:
            unpriced.append(call.model or "unknown")
            continue
        cached = usage.cache_read_tokens
        fresh = usage.input_tokens - cached if cached_included_in_input else usage.input_tokens
        total += (fresh * price["input"] + cached * price.get("cached_input", price["input"]) + usage.output_tokens * price["output"]) / 1_000_000
        cached_total += cached
    if len(unpriced) == len(calls):
        return EvalResult.skip(f"No price for model(s): {sorted(set(unpriced))}")
    score = 1.0 if total <= max_cost_usd else max(0.0, max_cost_usd / total)
    note = f"; unpriced calls: {sorted(set(unpriced))}" if unpriced else ""
    return EvalResult(
        score=score,
        passed=total <= max_cost_usd,
        explanation=f"cost_usd={total:.6f} over {len(calls)} LLM call(s), cached_tokens={cached_total} (budget {max_cost_usd}){note}",
    )
