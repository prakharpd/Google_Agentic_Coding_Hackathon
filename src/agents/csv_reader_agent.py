"""CSVReaderAgent implementation.

The agent loads a CSV file after it has passed the security check, extracts
basic schema information, generates a ydata‑profiling HTML report, and
returns a dictionary matching the contract defined in
``docs/agents/csv_reader_agent.md``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd
try:
    import sweetviz
except Exception:  # pragma: no cover – optional dependency
    sweetviz = None

from ..tools.file_reader import detect_encoding, load_csv
from ..utils.logger import log_info, log_error

__all__ = ["run_agent"]


def run_agent(filepath: str) -> Dict[str, object]:
    """Read a CSV, profile it, and return schema information.

    Parameters
    ----------
    filepath:
        Path to the CSV file.

    Returns
    -------
    dict
        ``{"shape": [rows, cols], "columns": [...], "dtypes": {...},
        "null_counts": {...}, "profile_path": "outputs/profile.html"}``
    """
    abs_path = Path(filepath).resolve()
    log_info(f"CSVReaderAgent: loading {abs_path}")

    if not abs_path.is_file():
        msg = f"File not found: {abs_path}"
        log_error(msg)
        raise FileNotFoundError(msg)

    encoding = detect_encoding(abs_path)
    log_info(f"Detected encoding: {encoding}")

    try:
        df = load_csv(str(abs_path))
    except Exception as exc:  # pragma: no cover – defensive
        log_error(f"Failed to read CSV: {exc}")
        raise

    # Basic schema extraction
    shape = list(df.shape)
    columns: List[str] = df.columns.tolist()
    dtypes: Dict[str, str] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    null_counts: Dict[str, int] = df.isna().sum().to_dict()

    # Generate profiling report if available
    profile_path = Path("outputs/profile.html")
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    if sweetviz is not None:
        try:
            report = sweetviz.analyze(df)
            report.show_html(filepath=profile_path, open_browser=False)
            log_info(f"Profiling report written to {profile_path}")
        except Exception as exc:  # pragma: no cover – defensive
            log_error(f"Failed to generate profiling report: {exc}")
            profile_path = None
    else:
        log_error("sweetviz is not installed; skipping profile report")
        profile_path = None

    result = {
        "shape": shape,
        "columns": columns,
        "dtypes": dtypes,
        "null_counts": null_counts,
        "profile_path": str(profile_path),
    }
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python csv_reader_agent.py <csv_path>")
        sys.exit(1)
    out = run_agent(sys.argv[1])
    print(json.dumps(out, indent=2))
# csv_reader_agent.py — scaffold via VS Code Agent Chat using prompt in docs/agents/csv_reader_agent.md
