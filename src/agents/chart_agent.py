"""ChartGeneratorAgent implementation.

The agent receives the EDA dictionary produced by ``eda_agent`` and asks the
``gpt-oss:20b-cloud`` model (via Ollama) to decide which chart type should be
generated for each column.  The chosen chart types are then rendered using
``matplotlib`` (for static PNG images) and ``plotly`` (for interactive HTML
charts).  All files are saved under ``outputs/charts/`` and the function
returns a dictionary matching the contract defined in
``docs/agents/chart_agent.md``.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

from ..tools.chart_generator import (
    create_bar_chart,
    create_boxplot,
    create_heatmap,
    create_histogram,
    create_line_chart,
    generate_synthetic_series,
)

import ollama  # noqa: F401 – required to satisfy the model usage requirement

from ..utils.logger import log_info, log_error

__all__ = ["run_agent"]


LLM_CALL_LOG = []


def _prompt_for_chart_types(
    eda: Dict[str, Any],
    only_columns: List[str] | None = None,
    df: pd.DataFrame | None = None,
) -> Dict[str, str]:
    """Ask the LLM to map each column to a chart type.

    The prompt provides the list of numeric columns (derived from the ``stats``
    section) and the correlation matrix.  The model is expected to return a JSON
    object where keys are column names and values are one of:
    ``histogram``, ``boxplot``, ``heatmap``, ``line``, ``bar``.
    """
    numeric_cols = list(eda.get("stats", {}).keys())
    if only_columns is not None:
        numeric_cols = [col for col in numeric_cols if col in only_columns]
    corr = eda.get("correlations", {})
    prompt = (
        "You are a data‑visualisation assistant. Given the following information, "
        "decide which chart type should be generated for each column. Return a JSON "
        "object mapping column name to one of: histogram, boxplot, heatmap, line, bar. "
        "Only include columns that appear in the stats section.\n\n"
        f"Numeric columns: {numeric_cols}\n"
        f"Correlation matrix: {json.dumps(corr)}"
    )
    try:
        response = ollama.generate(model="gpt-oss:20b-cloud", prompt=prompt, format="json")
        text = response.get("response", "")
        # Token accounting
        prompt_tokens = response.get('prompt_eval_count', 0) or 0
        completion_tokens = response.get('eval_count', 0) or 0
        total_tokens = prompt_tokens + completion_tokens
        is_fallback = not text or not text.strip()
        LLM_CALL_LOG.append({
            'agent': 'ChartGeneratorAgent',
            'tokens': total_tokens,
            'response': text,
            'fallback': is_fallback,
        })
        if not text or not text.strip():
            raise ValueError("Empty model response")
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response was not a JSON object")
        return parsed
    except Exception as exc:  # pragma: no cover – defensive
        log_error(f"LLM chart type decision failed: {exc}")

        if df is None:
            return {col: "histogram" for col in numeric_cols}

        fallback_columns = only_columns if only_columns is not None else list(df.columns)
        fallback_map: Dict[str, str] = {}
        for col in fallback_columns:
            if col not in df.columns:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                fallback_map[col] = "histogram"
            else:
                fallback_map[col] = "bar"
        if not fallback_map:
            fallback_map = {col: "histogram" for col in numeric_cols}
        return fallback_map


def run_agent(
    eda: Dict[str, Any],
    df: pd.DataFrame | None = None,
    only_columns: List[str] | None = None,
) -> Dict[str, List[str]]:
    """Generate charts based on EDA output.

    Parameters
    ----------
    eda:
        Dictionary produced by ``eda_agent``.
    df:
        Optional DataFrame for actual data visualization. If None, synthetic data is used.
    only_columns:
        Optional list of column names to generate charts for. If None, generate all.

    Returns
    -------
    dict
        ``{"charts": [list of file paths]}``
    """
    log_info("ChartGeneratorAgent: starting chart generation")

    out_dir = Path("outputs/charts")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chart_paths: List[str] = []

    # Ask LLM for chart type decisions per column
    chart_map = _prompt_for_chart_types(eda, only_columns=only_columns, df=df)

    # Generate charts for each column based on the chosen type
    for col, chart_type in chart_map.items():
        if only_columns is not None and col not in only_columns:
            continue
        try:
            if chart_type == "histogram":
                if df is not None and col in df.columns:
                    data = df[col].dropna().values
                else:
                    stats_col = eda["stats"].get(col, {})
                    mean = stats_col.get("mean", 0.0)
                    std = stats_col.get("std", 1.0)
                    data = generate_synthetic_series(mean, std)
                chart_paths.append(create_histogram(col, data, out_dir))
            elif chart_type == "boxplot":
                if df is not None and col in df.columns:
                    data = df[col].dropna().values
                else:
                    stats_col = eda["stats"].get(col, {})
                    mean = stats_col.get("mean", 0.0)
                    std = stats_col.get("std", 1.0)
                    data = generate_synthetic_series(mean, std)
                chart_paths.append(create_boxplot(col, data, out_dir))
            elif chart_type == "heatmap":
                chart_paths.append(create_heatmap(eda.get("correlations", {}), out_dir))
                break
            elif chart_type == "line":
                if df is not None and col in df.columns:
                    data = df[col].dropna().values
                else:
                    stats_col = eda["stats"].get(col, {})
                    mean = stats_col.get("mean", 0.0)
                    std = stats_col.get("std", 1.0)
                    data = generate_synthetic_series(mean, std)
                chart_paths.append(create_line_chart(col, data, out_dir))
            elif chart_type == "bar":
                nulls = eda.get("nulls", {})
                count = nulls.get(col, 0)
                categories = ["present", "missing"]
                counts = [100 - count, count]
                chart_paths.append(create_bar_chart(col, categories, counts, out_dir))
            else:
                log_error(f"Unsupported chart type '{chart_type}' for column {col}")
        except Exception as exc:  # pragma: no cover – defensive
            log_error(f"Failed to generate {chart_type} for {col}: {exc}")

    result = {"charts": chart_paths}
    log_info("ChartGeneratorAgent: chart generation complete")
    return result


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python chart_agent.py <eda_json_path>")
        sys.exit(1)
    eda_path = Path(sys.argv[1])
    if not eda_path.is_file():
        print(f"File not found: {eda_path}")
        sys.exit(1)
    with eda_path.open() as f:
        eda_data = json.load(f)
    out = run_agent(eda_data)
    print(json.dumps(out, indent=2))
# chart_agent.py — scaffold via VS Code Agent Chat using prompt in docs/agents/chart_agent.md
