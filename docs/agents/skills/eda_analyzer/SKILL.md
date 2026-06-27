---
name: EDAAnalyzerAgent
description: Compute exploratory data analysis metrics and produce a concise LLM-written summary.
triggers:
  positive:
    - csv.loaded
    - user.request.eda
  negative:
    - insufficient.numeric_columns
    - huge_dataset_without_sampling
tier: read-only
---

## Objective

Compute descriptive statistics, null and outlier analysis, correlations, and use an LLM to produce a human-readable EDA summary.

## Input/Output Contract

- Input: `df: pandas.DataFrame`
- Output: `{ "stats": {...}, "nulls": {...}, "correlations": {...}, "outliers": {...}, "llm_summary": str }`

## Step-by-step Workflow

1. Receive a `pandas.DataFrame` (fresh or loaded from CSV).
2. Compute `descriptive_stats`, `null_analysis`, `correlation_matrix`, and `outlier_detection` using `src/tools/stats.py`.
3. Assemble a payload and call the Ollama model (`gpt-oss:20b-cloud`) to generate a concise natural-language summary.
4. Return the structured EDA dict and log token/accounting metadata.

## Guardrails

- Limit LLM prompt size by only including computed metrics (not raw rows).
- If LLM call fails, return computed metrics and an empty or fallback `llm_summary` to avoid blocking downstream steps.
- Avoid exposing raw cell values in LLM prompts; include only aggregated statistics.

## References

- Specification: [docs/agents/eda_agent.md](docs/agents/eda_agent.md)
- Implementation: [src/agents/eda_agent.py](src/agents/eda_agent.py)
- Stats utilities: [src/tools/stats.py](src/tools/stats.py)
