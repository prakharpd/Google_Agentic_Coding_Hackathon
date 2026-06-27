---
name: ChartGeneratorAgent
description: Decide chart types from EDA and render charts (histogram, boxplot, heatmap, line, bar). Intended as draft for iteration.
triggers:
  positive:
    - eda.completed
    - user.request.charts
  negative:
    - no_numeric_columns
    - charting_dependency_missing
tier: draft-only
---

## Objective

Map EDA outputs to appropriate chart types and render visualizations to `outputs/charts/` using matplotlib/plotly. This skill is draft-only and subject to iteration.

## Input/Output Contract

- Input: `eda: dict`, optional `df: pandas.DataFrame`, optional `only_columns: list`
- Output: `{ "charts": ["outputs/charts/..."] }`

## Step-by-step Workflow

1. Receive EDA dictionary and optional DataFrame.
2. Ask LLM (`gpt-oss:20b-cloud`) to map columns to chart types via a JSON response.
3. For each column/chart type, generate the appropriate plot using helpers in `src/tools/chart_generator.py`.
4. Save charts to `outputs/charts/` (overwrite per run) and return paths.
5. Provide deterministic fallbacks when the LLM response is missing or invalid.

## Guardrails

- When LLM fails or returns invalid JSON, fall back to deterministic heuristics (numeric→histogram, categorical→bar).
- Do not assume DataFrame is present; support synthetic data generation for visuals.
- Keep chart files under `outputs/charts/` and overwrite between runs to avoid stale artifacts.

## References

- Specification: [docs/agents/chart_agent.md](docs/agents/chart_agent.md)
- Implementation: [src/agents/chart_agent.py](src/agents/chart_agent.py)
- Chart utilities: [src/tools/chart_generator.py](src/tools/chart_generator.py)
