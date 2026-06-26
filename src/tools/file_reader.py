from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import chardet
import pandas as pd


def detect_encoding(file_path: Path) -> str:
    """Detect the encoding of *file_path* using chardet."""
    with file_path.open("rb") as f:
        raw = f.read(1024 * 100)
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8") or "utf-8"


def load_csv(filepath: str) -> pd.DataFrame:
    """Load a CSV file using detected encoding."""
    abs_path = Path(filepath).resolve()
    encoding = detect_encoding(abs_path)
    return pd.read_csv(abs_path, encoding=encoding)
