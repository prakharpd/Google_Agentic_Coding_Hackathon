from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List

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

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

MIN_COLUMNS = 2
MAX_FILE_SIZE_MB = 50


def _contains_injection(text: str) -> bool:
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False


def validate_csv(filepath: str) -> Dict[str, object]:
    path = Path(filepath)
    if not path.is_file():
        return {"status": "BLOCKED", "reason": "File does not exist", "rows": 0, "cols": 0}

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {
            "status": "BLOCKED",
            "reason": f"File size {size_mb:.2f} MB exceeds limit of {MAX_FILE_SIZE_MB} MB",
            "rows": 0,
            "cols": 0,
        }

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

        for col in header:
            if _contains_injection(col):
                return {
                    "status": "BLOCKED",
                    "reason": f"Header column '{col}' contains a blocked pattern",
                    "rows": 0,
                    "cols": len(header),
                }

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
