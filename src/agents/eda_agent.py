"""EDAAnalyzerAgent implementation.

The agent receives a :class:`pandas.DataFrame`, computes a set of exploratory
data‑analysis metrics using only *pandas* and *scipy*, and then asks the
``gpt-oss:20b-cloud`` model (via the Ollama Python SDK) to generate a
human‑readable summary.  The result matches the contract defined in
``docs/agents/eda_agent.md``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

import ollama  # noqa: F401 – required to satisfy the model usage requirement

from ..tools.stats import (
    correlation_matrix,
    descriptive_stats,
    null_analysis,
    outlier_detection,
)
from ..utils.logger import log_info, log_error

__all__ = ["run_agent"]


LLM_CALL_LOG = []


def _generate_llm_summary(data: Dict[str, Any]) -> str:
    """Call the Ollama model to produce a natural‑language summary.

    The *data* dict is serialized to JSON and included in the prompt so the
    model can reference the computed metrics.
    """
    prompt = (
        "You are an analyst. Summarize the following exploratory data analysis results in a concise, "
        "human‑readable paragraph. Include key statistics, notable null patterns, any strong "
        "correlations, and outlier observations. Use the JSON payload below."
        "\n\n" + json.dumps(data, indent=2)
    )
    try:
        response = ollama.generate(model="gpt-oss:20b-cloud", prompt=prompt)
        # The Ollama SDK returns a dict with a 'response' key containing the text.
        response_text = response.get("response", "")
        # Extract token counts: prefer eval_count, else sum of prompt_eval_count + eval_count
        prompt_tokens = response.get('prompt_eval_count', 0) or 0
        completion_tokens = response.get('eval_count', 0) or 0
        total_tokens = prompt_tokens + completion_tokens
        is_fallback = not response_text or not response_text.strip()
        LLM_CALL_LOG.append({
            'agent': 'EDAAnalyzerAgent',
            'tokens': total_tokens,
            'response': response_text,
            'fallback': is_fallback,
        })
        return response_text
    except Exception as exc:  # pragma: no cover – defensive
        log_error(f"LLM summary generation failed: {exc}")
        return ""


def run_agent(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform EDA on *df* and return the structured result.

    The output matches the contract in ``docs/agents/eda_agent.md``.
    """
    log_info("EDAAnalyzerAgent: starting analysis")

    stats_res = descriptive_stats(df)
    nulls_res = null_analysis(df)
    corr_res = correlation_matrix(df)
    outliers_res = outlier_detection(df)

    # Prepare payload for LLM summary
    payload = {
        "stats": stats_res,
        "nulls": nulls_res,
        "correlations": corr_res,
        "outliers": outliers_res,
    }
    llm_summary = _generate_llm_summary(payload)

    result = {
        "stats": stats_res,
        "nulls": nulls_res,
        "correlations": corr_res,
        "outliers": outliers_res,
        "llm_summary": llm_summary,
    }
    log_info("EDAAnalyzerAgent: analysis complete")
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python eda_agent.py <csv_path>")
        sys.exit(1)
    csv_path = Path(sys.argv[1])
    if not csv_path.is_file():
        print(f"File not found: {csv_path}")
        sys.exit(1)
    df_input = pd.read_csv(csv_path)
    out = run_agent(df_input)
    print(json.dumps(out, indent=2))
# eda_agent.py — scaffold via VS Code Agent Chat using prompt in docs/agents/eda_agent.md
