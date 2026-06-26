"""Chart validation and regeneration orchestration using Google ADK patterns.

This module validates generated chart files against the original CSV data and
retries failed charts up to three times. The validation layer is composed of:

1. Rule-based checks: x-axis range, bin count (Sturges), file size, KDE peak alignment, skewness direction.
2. LLM feedback layer: passes failures to gpt-oss:20b-cloud for human-readable fix instructions.

Skewness interpretation:
  - skewness > 1: right-heavy distribution (left-side bars taller)
  - skewness < -1: left-heavy distribution (right-side bars taller)
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import ollama
import pandas as pd
from scipy.stats import skew

from ..utils.logger import log_info, log_error
from ..tools.chart_generator import calc_bins
from .chart_agent import run_agent as regenerate_charts, _prompt_for_chart_types

VALIDATION_REPORT = Path("outputs/validation_report.md")

__all__ = ["validate_and_retry"]


def _load_csv_fresh(csv_path: str) -> pd.DataFrame:
    """Load the CSV file fresh from disk using pandas."""
    try:
        return pd.read_csv(csv_path)
    except Exception as exc:
        log_error(f"Failed to load CSV for validation: {exc}")
        raise


def _load_png_metadata(png_path: Path) -> Dict[str, Any]:
    """Extract metadata from the PNG and optional pickle companion."""
    metadata: Dict[str, Any] = {"png_path": str(png_path)}
    pickle_path = png_path.with_suffix(".pkl")
    if pickle_path.is_file():
        try:
            with pickle_path.open("rb") as f:
                fig = pickle.load(f)
            axes = fig.get_axes()
            if axes:
                ax = axes[0]
                xlim = ax.get_xlim()
                bins = None
                # Detect histogram bins from patches if present
                patches = ax.patches
                if patches:
                    bins = len(patches)
                kde_line = None
                for line in ax.get_lines():
                    if line.get_label() == "KDE":
                        kde_line = line
                        break
                metadata.update({
                    "xlim": xlim,
                    "bin_count": bins,
                    "kde_line": kde_line,
                })
        except Exception as exc:
            log_error(f"Failed to load pickle metadata for {pickle_path}: {exc}")
    return metadata


def _rule_checks(csv_path: str, png_path: Path, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Perform rule-based validation checks on the chart."""
    df = _load_csv_fresh(csv_path)
    failures: List[Dict[str, Any]] = []

    # Extract column name from file path
    base_name = png_path.stem.replace("_histogram", "").replace("_boxplot", "").replace("_line", "").replace("_bar", "")
    if base_name not in df.columns:
        return failures

    col = base_name
    data = df[col].dropna().astype(float)
    n = len(data)
    data_stats = {
        "min": float(data.min()),
        "max": float(data.max()),
        "mean": float(data.mean()),
        "std": float(data.std(ddof=0)),
        "skewness": float(skew(data)),
    }

    # Check 1: x-axis range
    xlim = metadata.get("xlim")
    if xlim is not None:
        low, high = xlim
        tolerance = 0.05 * (data_stats["max"] - data_stats["min"])
        if low < data_stats["min"] - tolerance:
            failures.append({
                "chart_name": png_path.name,
                "check_failed": "x-axis min",
                "expected": f">= {data_stats['min'] - tolerance:.6f}",
                "actual": f"{low:.6f}",
            })
        if high > data_stats["max"] + tolerance:
            failures.append({
                "chart_name": png_path.name,
                "check_failed": "x-axis max",
                "expected": f"<= {data_stats['max'] + tolerance:.6f}",
                "actual": f"{high:.6f}",
            })

    # Check 2: Bin count using the shared tiered calc_bins function
    expected_bins = calc_bins(max(1, n))
    if metadata.get("bin_count") is not None and metadata["bin_count"] != expected_bins:
        failures.append({
            "chart_name": png_path.name,
            "check_failed": "bin count (Sturges)",
            "expected": expected_bins,
            "actual": metadata["bin_count"],
        })

    # Check 3: File size > 10KB
    file_size = png_path.stat().st_size
    if file_size <= 10 * 1024:
        failures.append({
            "chart_name": png_path.name,
            "check_failed": "file size",
            "expected": "> 10240 bytes",
            "actual": file_size,
        })

    # Check 4: KDE peak within 1 std of mean
    kde_line = metadata.get("kde_line")
    if kde_line is not None:
        xdata = np.array(kde_line.get_xdata())
        ydata = np.array(kde_line.get_ydata())
        if len(ydata) > 0:
            peak_idx = int(np.argmax(ydata))
            peak_x = float(xdata[peak_idx])
            if abs(peak_x - data_stats["mean"]) > 2 * data_stats["std"]:
                failures.append({
                    "chart_name": png_path.name,
                    "check_failed": "KDE peak alignment",
                    "expected": f"within 2 std of mean ({data_stats['mean']:.6f})",
                    "actual": f"{peak_x:.6f}",
                })
    else:
        failures.append({
            "chart_name": png_path.name,
            "check_failed": "KDE curve presence",
            "expected": "KDE overlay present",
            "actual": "not found",
        })

    return failures


def _llm_feedback(failures: List[Dict[str, Any]]) -> str:
    """Generate LLM-based human-readable feedback for chart validation failures."""
    prompt = (
        "You are a data visualization reviewer. Given these chart validation failures, "
        "write clear, concise fix instructions for the ChartAgent. Be specific: mention column name, "
        "what is wrong, and what the correct value should be. Keep it to 3-4 sentences.\n\n"
        + json.dumps(failures, indent=2)
    )
    try:
        response = ollama.generate(model="gpt-oss:20b-cloud", prompt=prompt)
        return response.get("response", "LLM feedback unavailable.")
    except Exception as exc:
        log_error(f"LLM feedback generation failed: {exc}")
        return "LLM feedback unavailable."


def _write_report(failures: List[Dict[str, Any]]) -> None:
    """Write validation report to outputs/validation_report.md with 'w' mode to overwrite."""
    rows = ["| Chart | Check | Status | Details |", "|---|---|---|---|"]
    for failure in failures:
        rows.append(
            f"| {failure['chart_name']} | {failure['check_failed']} | FAIL | expected={failure['expected']}, actual={failure['actual']} |"
        )
    # Use 'w' mode to delete and overwrite previous report
    VALIDATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_REPORT.open("w", encoding="utf-8") as f:
        f.write("# Chart Validation Report\n\n")
        f.write("\n".join(rows))
        f.write("\n")


def validate_and_retry(
    csv_path: str,
    eda: Dict[str, Any],
    df: pd.DataFrame,
) -> Dict[str, Any]:
    """Validate generated charts and retry failed ones up to 3 times.

    Parameters
    ----------
    csv_path:
        Path to the original CSV file (re-read fresh from disk).
    eda:
        EDA output dictionary from EDAAnalyzerAgent.
    df:
        DataFrame for chart regeneration.

    Returns
    -------
    dict
        ``{"status": "PASS"}`` if all charts pass, or ``{"status": "FAIL", "feedback": {...}}`` if retries exhausted.
    """
    csv_path_obj = Path(csv_path)
    failures: List[Dict[str, Any]] = []
    retry = 0
    feedback_dict: Dict[str, str] = {}

    while retry < 3:
        log_info(f"Chart validation attempt {retry + 1}")
        failures.clear()

        # Always re-read CSV fresh
        try:
            df_fresh = _load_csv_fresh(str(csv_path_obj))
        except Exception as exc:
            log_error(f"Failed to load CSV for validation attempt {retry + 1}: {exc}")
            return {"status": "FAIL", "reason": "CSV read error"}

        # Collect all PNG files and validate them
        png_paths = list(Path("outputs/charts").glob("*.png"))
        for png_path in png_paths:
            metadata = _load_png_metadata(png_path)
            failures.extend(_rule_checks(str(csv_path_obj), png_path, metadata))

        if not failures:
            log_info("All chart checks passed")
            # Write passing report
            VALIDATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
            with VALIDATION_REPORT.open("w", encoding="utf-8") as f:
                f.write("# Chart Validation Report\n\n")
                f.write("| Chart | Check | Status | Details |\n")
                f.write("|---|---|---|---|\n")
                f.write("| All charts | Comprehensive checks | PASS | All validations passed. |\n")
            return {"status": "PASS"}

        # Only retry on bin count failures; skewness direction is not regenerable.
        retryable_failures = [
            failure for failure in failures if failure["check_failed"] == "bin count (Sturges)"
        ]

        if not retryable_failures:
            log_error("Chart validation failed with non-regenerable issues; skipping retry")
            _write_report(failures)
            return {"status": "FAIL", "feedback": feedback_dict}

        # Generate LLM feedback only for retryable bin count failures
        feedback = _llm_feedback(retryable_failures)
        feedback_dict[f"attempt_{retry + 1}"] = feedback
        log_error(f"Chart validation failed on attempt {retry + 1}")
        log_error(feedback)

        # If this is the last retry, write the final report and exit
        if retry == 2:
            log_error("Chart validation failed after 3 retries")
            _write_report(failures)
            return {"status": "FAIL", "feedback": feedback_dict}

        # Regenerate only failed histogram charts for bin count failures
        failed_columns = sorted({
            failure["chart_name"].replace("_histogram.png", "").replace("_boxplot.png", "").replace("_line.html", "").replace("_bar.html", "")
            for failure in retryable_failures
        })
        log_info(f"Regenerating failed charts for columns: {failed_columns}")
        regenerate_charts(eda, df=df, only_columns=failed_columns)
        retry += 1

    # Fallback (should not reach here)
    log_error("Chart validation logic error: infinite loop protection triggered")
    return {"status": "FAIL", "reason": "Logic error"}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python chart_validator_agent.py <csv_path> <eda_json_path>")
        sys.exit(1)

    csv_input = sys.argv[1]
    eda_path = Path(sys.argv[2])

    if not eda_path.is_file():
        print(f"EDA file not found: {eda_path}")
        sys.exit(1)

    with eda_path.open("r", encoding="utf-8") as f:
        eda_output = json.load(f)

    df_input = pd.read_csv(csv_input)
    result = validate_and_retry(csv_input, eda_output, df_input)
    print(json.dumps(result, indent=2))
