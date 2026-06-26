from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from scipy.stats import gaussian_kde


def calc_bins(n: int) -> int:
    """Calculate chart bin counts using tiered rules based on sample size."""
    if n < 1:
        return 1
    if n < 200:
        return round(1 + math.log2(n))
    elif n < 1000:
        return round(2 * n**(1/3))
    else:
        return round(1 + 3.322 * math.log10(n))


def create_histogram(col: str, data: np.ndarray, out_dir: Path) -> str:
    n = len(data)
    bins = max(1, calc_bins(n))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(data, bins=bins, density=True, alpha=0.6, color="skyblue", edgecolor="black")

    try:
        kde = gaussian_kde(data)
        x_range = np.linspace(data.min(), data.max(), 200)
        ax.plot(x_range, kde(x_range), "r-", linewidth=2, label="KDE")
        ax.legend()
    except Exception:
        pass

    data_min = float(data.min())
    data_max = float(data.max())
    delta = max(1e-6, data_max - data_min)
    ax.set_xlim(data_min - 0.05 * delta, data_max + 0.05 * delta)

    ax.set_title(f"Histogram of {col} (n={n})")
    ax.set_xlabel(col)
    ax.set_ylabel("Density")
    ax.grid(True, alpha=0.3)

    path = out_dir / f"{col}_histogram.png"
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    pickle_path = path.with_suffix(".pkl")
    _save_figure_pickle(fig, pickle_path)
    plt.close()
    return str(path)


def _save_figure_pickle(fig: plt.Figure, path: Path) -> None:
    try:
        with path.open("wb") as f:
            pickle.dump(fig, f)
    except Exception:
        pass


def create_boxplot(col: str, data: np.ndarray, out_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.boxplot(data, vert=False)
    ax.set_title(f"Boxplot of {col}")
    ax.set_xlabel(col)
    path = out_dir / f"{col}_boxplot.png"
    plt.tight_layout()
    plt.savefig(path)
    pickle_path = path.with_suffix(".pkl")
    _save_figure_pickle(fig, pickle_path)
    plt.close()
    return str(path)


def create_heatmap(corr: Dict[str, Dict[str, float]], out_dir: Path) -> str:
    df_corr = pd.DataFrame(corr)
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(df_corr, cmap="viridis", aspect="auto")
    ax.set_title("Correlation Heatmap")
    fig.colorbar(cax)
    path = out_dir / "correlation_heatmap.png"
    plt.tight_layout()
    plt.savefig(path)
    pickle_path = path.with_suffix(".pkl")
    _save_figure_pickle(fig, pickle_path)
    plt.close()
    return str(path)


def create_line_chart(col: str, data: np.ndarray, out_dir: Path) -> str:
    fig = px.line(x=range(len(data)), y=data, labels={"x": "Index", "y": col}, title=f"Line chart of {col}")
    path = out_dir / f"{col}_line.html"
    pio.write_html(fig, file=str(path), auto_open=False)
    return str(path)


def create_bar_chart(col: str, categories: List[str], counts: List[int], out_dir: Path) -> str:
    fig = px.bar(x=categories, y=counts, labels={"x": col, "y": "Count"}, title=f"Bar chart of {col}")
    path = out_dir / f"{col}_bar.html"
    pio.write_html(fig, file=str(path), auto_open=False)
    return str(path)


def generate_synthetic_series(mean: float, std: float, size: int = 200) -> np.ndarray:
    return np.random.normal(loc=mean, scale=std, size=size)


def create_kde_plot(col: str, data: np.ndarray, out_dir: Path) -> str:
    fig = px.histogram(
        x=data,
        nbins=calc_bins(len(data)),
        marginal="box",
        opacity=0.8,
        title=f"Histogram: {col}",
        color_discrete_sequence=["#00ffd5"],
        template="plotly_dark",
    )
    fig.update_layout(hovermode="x unified", paper_bgcolor="#07080f", plot_bgcolor="#07080f")
    path = out_dir / f"{col}_histogram.html"
    pio.write_html(fig, file=str(path), auto_open=False)
    return str(path)
