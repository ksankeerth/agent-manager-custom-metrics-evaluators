from amp_evaluation import EvalResult, Param
from amp_evaluation.trace.models import Trace


def evaluate(
    trace: Trace,
    error_prefix: str = Param(default="ERROR", description="Tool results starting with this text count as failures"),
) -> EvalResult:
    tools = trace.get_tool_calls()
    if not tools:
        return EvalResult.skip("No tool calls in this trace")
    failed = [
        t.name
        for t in tools
        if t.metrics.error or str(t.result or "").lstrip().upper().startswith(error_prefix.upper())
    ]
    score = 1.0 - len(failed) / len(tools)
    detail = f": {', '.join(failed)}" if failed else ""
    return EvalResult(
        score=score,
        passed=not failed,
        explanation=f"tool_failures={len(failed)}/{len(tools)} (failure_rate={len(failed) / len(tools):.0%}){detail}",
    )
