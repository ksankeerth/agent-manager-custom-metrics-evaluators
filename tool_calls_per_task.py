from amp_evaluation import EvalResult, Param
from amp_evaluation.trace.models import Trace


def evaluate(
    trace: Trace,
    max_tool_calls: int = Param(default=4, description="Tool calls a task may use before the score degrades", min=1),
) -> EvalResult:
    tools = trace.get_tool_calls()
    calls = len(tools)
    names = ", ".join(t.name for t in tools) or "none"
    score = 1.0 if calls <= max_tool_calls else max(0.0, max_tool_calls / calls)
    return EvalResult(
        score=score,
        passed=calls <= max_tool_calls,
        explanation=f"tool_calls={calls} (budget {max_tool_calls}): {names}",
    )
