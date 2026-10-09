# Agent Manager custom evaluators

Sample custom evaluators for [WSO2 Agent Manager](https://github.com/wso2/agent-manager), showing how to write code and LLM-judge evaluators for agent metrics. They are examples to learn from and adapt, not a replacement for the built-in evaluators.

**Use a built-in evaluator first.** Agent Manager ships 24 built-ins, and most agent metrics are covered by one of them. Write a custom evaluator only when no built-in fits your use case, as with three of the samples below.

They were written for the `samples/it-helpdesk-agent` sample and run end to end on a local Agent Manager, with a local Ollama `gemma4:e2b` as both the agent's model and the LLM judge.

![How evaluators score traces](screenshots/00-evaluation-flow.png)

## Built-in or custom?

| Metric | Use this built-in | Custom sample here | When to use the custom sample |
| --- | --- | --- | --- |
| Tokens per task | `token_efficiency` | none | Use the built-in |
| Model calls per agent | `iteration_efficiency` | none | Use the built-in |
| Round-trip time | `latency_performance` | none | Use the built-in |
| Tool calls per task | none | `tool-calls-per-task` | No built-in counts tool calls against a budget |
| Steps per task (model + tool calls) | `path_efficiency` (LLM judge, qualitative) | `steps-per-task` | You want a count against a budget, not a judgement |
| Tool failure rate | `step_success_rate` | `tool-failure-rate` | Your tools report failure as text (for example `ERROR: …`) instead of raising |
| Human handoffs | `tool_coverage` with `required_tools` set to your handoff tool (scores 1 when a handoff happened) | `self-service-resolution` | You want "higher is better", so the mean reads as a self-service rate |
| PII exposure | `safety` (LLM judge, includes privacy) or `content_safety` with `prohibited_patterns` | `pii-exposure` | You want PII the user typed in themselves not to count |
| Task success | `completeness`, `helpfulness` | `task-success` | A correct follow-up question should count as success, and claims should be checked against tool results |
| Business rules | `instruction_following` (checks the rules in the agent's system prompt) | `helpdesk-policy-compliance` | Your rules aren't in the system prompt, or you want them checked independently of it |

Why `tool-failure-rate` exists: `step_success_rate` only counts tool calls whose span is marked as an error. The helpdesk tools return `ERROR: …` text instead of raising. On the same 26 traces, `step_success_rate` reported 100% success, while `tool-failure-rate` found 2 failing traces.

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

## Use them

To create custom evaluators and attach them to monitors, follow the Agent Manager docs:

- [Evaluation concepts](https://wso2.com/agent-platform/docs/cloud/concepts/evaluation/)
- [Custom evaluators guide](https://wso2.github.io/docs-agent-platform/cloud/guides/custom-evaluators/)

Paste a sample's contents as the evaluator source, with the type, level and parameters from the table above. A setup that works well:
- **Ops monitor:** rule-based built-ins (`token_efficiency`, `iteration_efficiency`, `latency_performance`) plus any custom code evaluators you need, every 5 to 15 minutes.
- **Quality monitor:** LLM judges, built-in or custom, hourly. It needs an LLM provider.

### Adapting them to your agent

- Set `handoff_tools` and `error_prefix` to match your agent's tool names and failure format.
- Rewrite the business rules in `helpdesk_policy_compliance.txt`; any extra parameter you add becomes a `{variable}` in the prompt.
- Change budgets per monitor in the evaluator config; no code change is needed.

## Results

On 26 real traces from the helpdesk sample. The ops monitor screenshots come from an earlier set that also included custom versions of the token, model-call and latency metrics; use the built-ins above for those instead.

![Ops monitor overview](screenshots/01-ops-monitor-overview.png)

![Ops monitor trends and per-agent breakdown](screenshots/02-ops-monitor-trends.png)

![Quality monitor: task success and policy compliance, average 89.58%](screenshots/03-quality-monitor-overview.png)

![Quality monitor trends](screenshots/04-quality-monitor-trends.png)

## Things to know

- **Scores only.** Scores must be between 0 and 1, so counts are scored against a budget, and the raw number only appears in the explanation.
- **Failed requests aren't counted.** By default, failed requests are skipped rather than scored, so a broken agent shows more skips, not lower scores.
- **Small judges are unreliable.** The judges here ran on a 2B model, which gave inconsistent and sometimes wrong verdicts. Use a stronger judge model and spot-check low scores.
- **Not real-time.** Monitors are batch jobs: at least a 5-minute interval, no alerting, and one agent per monitor.
