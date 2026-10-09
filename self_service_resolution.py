from amp_evaluation import EvalResult, Param
from amp_evaluation.trace.models import Trace


def evaluate(
    trace: Trace,
    handoff_tools: str = Param(default="escalate_to_l2", description="Comma-separated tool names that hand the task to a human"),
) -> EvalResult:
    handoff_names = {n.strip() for n in handoff_tools.split(",") if n.strip()}
    handoffs = [t.name for t in trace.get_tool_calls() if t.name in handoff_names]
    if handoffs:
        return EvalResult(
            score=0.0,
            passed=False,
            explanation=f"handoff=true via {', '.join(handoffs)}",
        )
    return EvalResult(score=1.0, passed=True, explanation="handoff=false (handled without a human)")
