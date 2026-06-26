"""Summary Agent implementation using Google ADK patterns.

This agent generates the final human-readable summary report by reading fresh
data from the CSV and current run's EDA/chart outputs. It uses gpt-oss:20b-cloud via
the Ollama Python SDK to produce a polished markdown report with five sections:
1. Dataset overview (shape, columns, dtypes, null counts, min/max)
2. EDA findings per column (mean, std, skewness, kurtosis)
3. Chart descriptions per plot
4. Top 3 business insights
5. Data quality notes

The report is saved to outputs/summary.md (always overwritten with 'w' mode).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import ollama
import pandas as pd

from ..utils.logger import log_info, log_error

__all__ = ["run_agent"]


LLM_CALL_LOG = []


def _load_csv_fresh(csv_path: str) -> pd.DataFrame:
    """Load CSV file fresh from disk using pandas."""
    try:
        return pd.read_csv(csv_path)
    except Exception as exc:
        log_error(f"Failed to load CSV for summary: {exc}")
        raise


def _extract_csv_overview(df: pd.DataFrame) -> Dict[str, Any]:
    """Extract fresh dataset overview directly from CSV."""
    overview = {
        "shape": list(df.shape),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isna().sum().to_dict(),
        "numeric_ranges": {},
    }

    # Add min/max for numeric columns
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        try:
            overview["numeric_ranges"][col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
            }
        except Exception:
            pass

    return overview


def _read_chart_paths(chart_dir: Path) -> List[str]:
    """Read all chart file paths from the output directory."""
    if not chart_dir.is_dir():
        return []
    return sorted([str(p) for p in chart_dir.glob("*.*") if p.suffix.lower() in {".png", ".html"}])


def _build_summary_prompt(
    csv_overview: Dict[str, Any],
    eda_output: Dict[str, Any],
    chart_paths: List[str],
) -> str:
    """Build the prompt for gpt-oss:20b-cloud to generate the summary."""
    eda_stats = eda_output.get("stats", {})
    chart_descriptions = "\n".join([f"- {Path(p).name}" for p in chart_paths]) if chart_paths else "- No charts generated"

    prompt = (
        "You are a business analyst. Generate a professional markdown summary report containing EXACTLY these 5 sections:\n\n"
        "1. **Dataset Overview** – Include shape, column count, data types, null value counts, and numeric ranges (min/max).\n"
        "2. **EDA Findings Per Column** – For each column, report mean, std, skewness, and kurtosis if available.\n"
        "3. **Chart Descriptions** – List and briefly describe each generated chart.\n"
        "4. **Top 3 Business Insights** – Identify key patterns, anomalies, or opportunities in the data.\n"
        "5. **Data Quality Notes** – Discuss data completeness, outliers, and recommended data cleaning steps.\n\n"
        "Use the following data:\n\n"
        "Dataset Overview (from fresh CSV read):\n"
        f"{json.dumps(csv_overview, indent=2)}\n\n"
        "EDA Statistics (from current run):\n"
        f"{json.dumps(eda_stats, indent=2)}\n\n"
        "Generated Charts:\n"
        f"{chart_descriptions}\n\n"
        "Generate the report in markdown. Use headings, bullet points, and professional language suitable for business stakeholders."
    )
    return prompt


def _generate_summary_via_llm(prompt: str) -> str:
    """Call gpt-oss:20b-cloud via ollama to generate the summary."""
    try:
        response = ollama.generate(model="gpt-oss:20b-cloud", prompt=prompt)
        summary_text = response.get("response", "")
        # Token accounting
        total_tokens = response.get('eval_count')
        if not total_tokens:
            total_tokens = response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
        is_fallback = not summary_text or not summary_text.strip()
        LLM_CALL_LOG.append({
            'agent': 'SummaryAgent',
            'tokens': total_tokens,
            'response': summary_text,
            'fallback': is_fallback,
        })
        if not summary_text or not summary_text.strip():
            log_error("LLM returned empty response for summary generation")
            return _fallback_summary()
        return summary_text
    except Exception as exc:
        log_error(f"Failed to generate summary via Ollama: {exc}")
        return _fallback_summary()


def _fallback_summary() -> str:
    """Return a minimal fallback summary if LLM fails."""
    return (
        "# Data Analysis Summary\n\n"
        "The data analysis pipeline completed with chart generation and validation. "
        "Please refer to the validation report and individual chart outputs for details.\n"
    )


def run_agent(
    eda_output: Dict[str, Any],
    csv_path: str,
    charts_dir: Path = Path("outputs/charts"),
    output_path: Path = Path("outputs/summary.md"),
) -> Dict[str, str]:
    """Generate the final summary markdown report.

    Parameters
    ----------
    eda_output:
        Dictionary output from EDAAnalyzerAgent (current run).
    csv_path:
        Path to the original CSV file (re-read fresh).
    charts_dir:
        Directory containing generated chart files.
    output_path:
        Path where the summary markdown should be saved.

    Returns
    -------
    dict
        Result metadata including the output path.
    """
    try:
        # Load CSV fresh from disk
        df = _load_csv_fresh(csv_path)
        log_info("SummaryAgent: loaded CSV fresh from disk")

        # Extract dataset overview from fresh CSV
        csv_overview = _extract_csv_overview(df)
        log_info("SummaryAgent: extracted dataset overview from CSV")

        # Read chart paths from current run
        chart_paths = _read_chart_paths(charts_dir)
        log_info(f"SummaryAgent: found {len(chart_paths)} chart(s)")

        # Build prompt and generate summary
        prompt = _build_summary_prompt(csv_overview, eda_output, chart_paths)
        summary_md = _generate_summary_via_llm(prompt)
        log_info("SummaryAgent: generated summary via gpt-oss:20b-cloud")

        # Write summary to outputs/summary.md (always overwrite with 'w' mode)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(summary_md)
        log_info(f"SummaryAgent completed and wrote report to {output_path}")

        return {"status": "COMPLETED", "summary_path": str(output_path)}

    except Exception as exc:
        log_error(f"SummaryAgent failed: {exc}")
        return {"status": "FAILED", "reason": str(exc)}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python summary_agent.py <csv_path> <eda_json_path>")
        sys.exit(1)

    csv_input = sys.argv[1]
    eda_path = Path(sys.argv[2])

    if not eda_path.is_file():
        print(f"EDA file not found: {eda_path}")
        sys.exit(1)

    with eda_path.open("r", encoding="utf-8") as f:
        eda_output = json.load(f)

    result = run_agent(eda_output, csv_input)
    print(json.dumps(result, indent=2))
