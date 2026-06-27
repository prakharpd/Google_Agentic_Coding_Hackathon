---
name: SummaryAgent
description: Produce a polished markdown summary report combining EDA, validation output, and chart descriptions for business stakeholders.
triggers:
  positive:
    - pipeline.post_validation
    - user.request.summary
  negative:
    - missing_eda_output
    - failed_chart_validation
tier: draft-only
---

## Objective

Generate a stakeholder-ready markdown report with dataset overview, per-column EDA findings, chart summaries, top 3 business insights, and data quality notes.

## Input/Output Contract

- Input: `eda_output: dict`, `csv_path: str`, optional `charts_dir: Path`
- Output: `{ "status": "COMPLETED" | "FAILED", "summary_path": str }`

## Step-by-step Workflow

1. Re-read the CSV fresh to extract an authoritative dataset overview (shape, dtypes, null counts, numeric ranges).
2. Read the EDA output produced in the current run.
3. List generated chart files and include their filenames in the prompt.
4. Build a structured prompt and call `gpt-oss:20b-cloud` to produce a five-section markdown report.
5. Write the report to `outputs/summary.md` (overwrite) and return the path.

## Guardrails

- Keep prompts limited to aggregated metrics and chart filenames; do not include raw rows of data.
- If the LLM returns an empty response, use a minimal fallback summary so the pipeline remains observable.
- Avoid leaking any sensitive cell contents into the LLM prompt; use fresh CSV overview aggregates only.

## References

- Specification: [docs/agents/summary_agent.md](docs/agents/summary_agent.md)
- Implementation: [src/agents/summary_agent.py](src/agents/summary_agent.py)
