# Agent Manager custom evaluators

Reference custom evaluators for [WSO2 Agent Manager](https://github.com/wso2/agent-manager). They cover agent metrics that the built-in evaluators don't: tool calls per task, steps per task, tool failures reported as text, human handoffs, PII exposure, task success and business-rule compliance.

They were written for the `samples/it-helpdesk-agent` sample and run end to end on a local Agent Manager, with a local Ollama `gemma4:e2b` as both the agent's model and the LLM judge.

![How evaluators score traces](screenshots/00-evaluation-flow.png)

## What's here

| Evaluator | File | Type | Level | Measures | Parameters (default) |
| --- | --- | --- | --- | --- | --- |
| `tool-calls-per-task` | `tool_calls_per_task.py` | code | trace | Tool calls per task vs a budget | `max_tool_calls` (4) |
| `steps-per-task` | `steps_per_task.py` | code | trace | Model calls + tool calls per task vs a budget | `max_steps` (8) |
| `tool-failure-rate` | `tool_failure_rate.py` | code | trace | Share of tool calls that succeeded, counting results that start with `ERROR` as failures | `error_prefix` ("ERROR") |
| `self-service-resolution` | `self_service_resolution.py` | code | trace | Handled without a human handoff | `handoff_tools` ("escalate_to_l2") |
| `pii-exposure` | `pii_exposure.py` | code | trace | No email, phone, SSN or card data in the reply that the user didn't supply | `allow_echo` (true) |
| `task-success` | `task_success.txt` | llm_judge | trace | Was the request handled in this turn | base judge parameters |
| `helpdesk-policy-compliance` | `helpdesk_policy_compliance.txt` | llm_judge | trace | Business rules: identity first, admin resets refused, facts from tools, no other employee's PII | base judge parameters, `company` ("AcmeCorp") |

`manifest.json` lists each evaluator's identifier, display name, description, level, tags and parameter schema.

Every score is 0 to 1, with higher meaning better. The raw value, such as `tool_failures=1/2 (failure_rate=50%): request_software_access`, goes in the explanation shown on each trace.

### Use the built-ins for these

Some agent metrics are already covered by Agent Manager's built-in evaluators, so they aren't repeated here:

| Metric | Built-in evaluator |
| --- | --- |
| Tokens per task | `token_efficiency` |
| Model calls per agent | `iteration_efficiency` |
| Round-trip time to completion | `latency_performance` |

The built-in `step_success_rate` is *not* a substitute for `tool-failure-rate`. It only counts tool calls whose span is marked as an error. On the same 26 traces it reported 100% success, while `tool-failure-rate` found 2 failing traces where the tools returned `ERROR: …` text instead of raising.

## Use them

To create custom evaluators and attach them to monitors, follow the Agent Manager docs:

- [Evaluation concepts](https://wso2.com/agent-platform/docs/cloud/concepts/evaluation/)
- [Custom evaluators guide](https://wso2.github.io/docs-agent-platform/cloud/guides/custom-evaluators/)

Paste each file's contents as the evaluator source, with the type, level and parameters from the table above. A setup that works well:
- **Ops monitor:** the code evaluators plus the built-ins above, every 5 to 15 minutes.
- **Quality monitor:** the two LLM judges, hourly. It needs an LLM provider.

### Adapting them to your agent

- Set `handoff_tools` and `error_prefix` to match your agent's tool names and failure format.
- Rewrite the business rules in `helpdesk_policy_compliance.txt`; any extra parameter you add becomes a `{variable}` in the prompt.
- Change budgets per monitor in the evaluator config; no code change is needed.

## Results

On 26 real traces from the helpdesk sample. The ops monitor screenshots come from an earlier set that also included custom versions of the token, model-call and latency metrics, which have since been replaced by the built-ins above.

![Ops monitor overview](screenshots/01-ops-monitor-overview.png)

![Ops monitor trends and per-agent breakdown](screenshots/02-ops-monitor-trends.png)

![Quality monitor: task success and policy compliance, average 89.58%](screenshots/03-quality-monitor-overview.png)

![Quality monitor trends](screenshots/04-quality-monitor-trends.png)

## Things to know

- **Scores only.** Scores must be between 0 and 1, so counts are scored against a budget, and the raw number only appears in the explanation.
- **Failed requests aren't counted.** By default, failed requests are skipped rather than scored, so a broken agent shows more skips, not lower scores.
- **Small judges are unreliable.** The judges here ran on a 2B model, which gave inconsistent and sometimes wrong verdicts. Use a stronger judge model and spot-check low scores.
- **Not real-time.** Monitors are batch jobs: at least a 5-minute interval, no alerting, and one agent per monitor.
