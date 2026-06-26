"""Security validator for CSV uploads.

The validator implements the injection‑pattern checks described in
``docs/security.md``.  It exposes a single function
:func:`validate_csv` that returns a dictionary with the status, reason, and
basic file statistics.

The module is intentionally lightweight – it only reads the file header and
string columns to look for known malicious patterns.  The function is
designed to be called by :mod:`src/agents/security_agent.py`.
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Dict, List

# Import the pattern list from the docs file for consistency.
# The patterns are defined in ``docs/security.md`` under the
# ``INJECTION_PATTERNS`` section.
INJECTION_PATTERNS: List[str] = [
    r"ignore previous",
    r"system prompt",
    r"<script",
    r"DROP TABLE",
    r"__import__",
    r"os\.system",
    r"eval\(",
    r"exec\(",
]

# Compile the regexes once for performance.
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Validation constants
MIN_COLUMNS = 2
MAX_FILE_SIZE_MB = 50


def _contains_injection(text: str) -> bool:
    """Return ``True`` if *text* matches any injection pattern."""
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False


def validate_csv(filepath: str) -> Dict[str, object]:
    """Validate a CSV file for security concerns.

    Parameters
    ----------
    filepath:
        Path to the CSV file.

    Returns
    -------
    dict
        ``{"status": "PASSED"|"BLOCKED", "reason": str, "rows": int, "cols": int}``
    """
    path = Path(filepath)
    if not path.is_file():
        return {"status": "BLOCKED", "reason": "File does not exist", "rows": 0, "cols": 0}

    # Size check
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "status": "BLOCKED",
            "reason": f"File size {size_mb:.2f} MB exceeds limit of {MAX_FILE_SIZE_MB} MB",
            "rows": 0,
            "cols": 0,
        }

    # Read header and a few rows to inspect string values
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return {"status": "BLOCKED", "reason": "Empty file", "rows": 0, "cols": 0}

        if len(header) < MIN_COLUMNS:
            return {
                "status": "BLOCKED",
                "reason": f"Header has {len(header)} columns; minimum required is {MIN_COLUMNS}",
                "rows": 0,
                "cols": len(header),
            }

        # Check header for injection patterns
        for col in header:
            if _contains_injection(col):
                return {
                    "status": "BLOCKED",
                    "reason": f"Header column '{col}' contains a blocked pattern",
                    "rows": 0,
                    "cols": len(header),
                }

        # Inspect first 100 rows for string columns
        rows = 0
        for row in reader:
            rows += 1
            if rows >= 100:
                break
            for cell in row:
                if isinstance(cell, str) and _contains_injection(cell):
                    return {
                        "status": "BLOCKED",
                        "reason": "String cell contains a blocked pattern",
                        "rows": rows,
                        "cols": len(header),
                    }

    return {"status": "PASSED", "reason": "No issues detected", "rows": rows, "cols": len(header)}

# Simple test when run directly
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python validator.py <csv_path>")
        sys.exit(1)
    result = validate_csv(sys.argv[1])
    print(result)
