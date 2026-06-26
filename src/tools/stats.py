from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from scipy import stats


def descriptive_stats(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Return descriptive statistics for numeric columns."""
    stats_dict: Dict[str, Dict[str, Any]] = {}
    numeric = df.select_dtypes(include="number")
    for col in numeric.columns:
        series = numeric[col]
        stats_dict[col] = {
            "mean": series.mean(),
            "median": series.median(),
            "std": series.std(ddof=0),
            "skew": stats.skew(series, bias=False),
            "kurtosis": stats.kurtosis(series, bias=False),
        }
    return stats_dict


def outlier_detection(df: pd.DataFrame) -> Dict[str, List[int]]:
    """Detect outliers using the IQR method."""
    outliers: Dict[str, List[int]] = {}
    numeric = df.select_dtypes(include="number")
    for col in numeric.columns:
        series = numeric[col]
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (series < lower) | (series > upper)
        outlier_idxs = list(mask[mask].index)
        if outlier_idxs:
            outliers[col] = outlier_idxs
    return outliers


def null_analysis(df: pd.DataFrame) -> Dict[str, int]:
    return df.isna().sum().to_dict()


def correlation_matrix(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    numeric = df.select_dtypes(include="number")
    corr = numeric.corr()
    return {col: corr[col].to_dict() for col in corr.columns}
