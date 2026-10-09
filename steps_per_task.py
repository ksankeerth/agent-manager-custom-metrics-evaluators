from amp_evaluation import EvalResult, Param
from amp_evaluation.trace.models import Trace


def evaluate(
    trace: Trace,
    max_steps: int = Param(default=8, description="LLM + tool steps a task may take before the score degrades", min=1),
) -> EvalResult:
    llm_steps = len(trace.get_llm_calls())
    tool_steps = len(trace.get_tool_calls())
    steps = llm_steps + tool_steps
    if steps == 0:
        return EvalResult.skip("No LLM or tool steps in this trace")
    score = 1.0 if steps <= max_steps else max(0.0, max_steps / steps)
    return EvalResult(
        score=score,
        passed=steps <= max_steps,
        explanation=f"steps={steps} (llm={llm_steps}, tool={tool_steps}; budget {max_steps})",
    )
