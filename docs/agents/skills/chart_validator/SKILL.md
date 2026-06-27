---
name: ChartValidatorAgent
description: Validate generated charts against source CSV using rule-based checks and an LLM feedback layer; orchestrates retries when feasible.
triggers:
  positive:
    - charts.generated
    - pipeline.post_chart_generation
  negative:
    - missing_chart_files
    - non_regenerable_failure
tier: read-only
---

## Objective

Ensure visualizations accurately reflect the underlying data by running deterministic checks (x-axis range, bin count, file size, KDE alignment, skewness) and producing human-readable LLM feedback for retryable failures.

## Input/Output Contract

- Input: `{ "csv_path": str, "eda": dict, "df": pandas.DataFrame }`
- Output: `{ "status": "PASS" | "FAIL", "feedback": dict | null }`

## Step-by-step Workflow

1. Re-read the CSV fresh from disk for authoritative validation.
2. For each chart file in `outputs/charts/*.png`, load optional pickle metadata and perform rule-based checks (see `src/agents/chart_validator_agent.py`).
3. Collect failures; if failures are retryable (bin-count), call the LLM to generate concise fix instructions and attempt regeneration up to 3 times.
4. If non-retryable issues exist (KDE missing, skewness direction mismatch), write a final report and halt the pipeline.
5. Write `outputs/validation_report.md` summarising results and return status.

## Guardrails

- Only retry regeneration for clearly retryable issues (bin count). Non-regenerable failures must block or surface to users.
- LLM feedback must be concise and targeted; do not include raw data dumps in prompts.
- Always overwrite validation reports (`w` mode) to avoid appending stale results.

## References

- Specification: [docs/agents/chart_validator_agent.md](docs/agents/chart_validator_agent.md)
- Implementation: [src/agents/chart_validator_agent.py](src/agents/chart_validator_agent.py)
- Regeneration helper: [src/agents/chart_agent.py](src/agents/chart_agent.py)
