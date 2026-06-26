from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import os

if os.path.exists("outputs/eval_report.json"):
    with open("outputs/eval_report.json") as f:
        ev = json.load(f)
    st.session_state["total_time"] = f"{ev['pipeline_duration_sec']:.1f}s"
    st.session_state["slowest_agent"] = f"{ev['slowest_agent']} ({ev['slowest_agent_sec']:.1f}s)"
    st.session_state["llm_accuracy"] = f"{ev['llm_accuracy_score']}%"
    st.session_state["fallback_rate"] = f"{ev['llm_fallback_rate']}%"
    st.session_state["retries"] = ev['chart_validation_retries']
    st.session_state["security_status"] = ev['security_status']
    st.session_state["total_tokens"] = f"{ev['total_llm_tokens']:,}"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.agents import orchestrator  # type: ignore

OUTPUT_SUMMARY = PROJECT_ROOT / "outputs" / "summary.json"
SUMMARY_MD = PROJECT_ROOT / "outputs" / "summary.md"
AUDIT_LOG = PROJECT_ROOT / "audit.log"
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"

AGENT_ORDER = [
    "Security",
    "CSVReader",
    "EDA",
    "ChartGenerator",
    "ChartValidator",
    "Summary",
]

STATUS_BADGES = {
    "pending": "<span class='status-badge pending'>PENDING</span>",
    "running": "<span class='status-badge running'>RUNNING</span>",
    "passed": "<span class='status-badge pass'>PASSED</span>",
    "failed": "<span class='status-badge fail'>FAILED</span>",
    "blocked": "<span class='status-badge blocked'>BLOCKED</span>",
    "skipped": "<span class='status-badge skipped'>SKIPPED</span>",
}

st.set_page_config(
    page_title="AI Business Analyst Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        font-family: Inter, system-ui, sans-serif;
    }
    body {
        background: #0a0a0f;
        color: #e6f7ff;
    }
    .stApp, .main, .block-container, .css-18e3th9, .css-k008qs {
        background: transparent !important;
    }
    .block-container {
        padding: 2rem 1rem 1.35rem 1rem !important;
        max-width: 100% !important;
    }
    .css-1d391kg {
        padding-top: 1.5rem !important;
    }
    .css-1dp5vir, .css-1lz4f7l, .css-13sdm1f {
        background: transparent !important;
    }
    [data-testid="stSidebar"] {
        background: #07080f !important;
        color: #e6f7ff;
        border-right: 1px solid rgba(0,255,220,0.12);
    }
    .stSidebar .css-1d391kg {
        padding-top: 1rem !important;
    }
    .metric-card {
        background: rgba(10, 15, 28, 0.95);
        border: 1px solid rgba(0, 255, 220, 0.16);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 18px 50px rgba(0, 255, 220, 0.05);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-card .card-label {
        font-size: 0.85rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #7ce2ff;
        margin-bottom: 0.5rem;
    }
    .metric-card .card-value {
        font-size: 2.6rem;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .metric-card .card-note {
        color: #9ef0ff;
        margin-top: 0.35rem;
        font-size: 0.95rem;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.55rem 0.9rem;
        border-radius: 999px;
        border: 1px solid rgba(0, 255, 220, 0.22);
        font-size: 0.85rem;
        font-weight: 700;
        color: #9dfaf8;
        background: rgba(0, 255, 220, 0.08);
    }
    .status-badge.pass { background: rgba(32, 201, 151, 0.18); border-color: rgba(32, 201, 151, 0.3); color: #c4ffe5; }
    .status-badge.fail { background: rgba(220, 53, 69, 0.18); border-color: rgba(220, 53, 69, 0.3); color: #ffc7c9; }
    .status-badge.blocked { background: rgba(220, 53, 69, 0.18); border-color: rgba(220, 53, 69, 0.3); color: #ffc7c9; }
    .status-badge.skipped { background: rgba(108, 117, 125, 0.18); border-color: rgba(108, 117, 125, 0.3); color: #c3cfd9; }
    .status-badge.pending { background: rgba(255, 179, 0, 0.18); border-color: rgba(255, 179, 0, 0.3); color: #ffeab0; }
    .status-badge.running { background: rgba(0, 123, 255, 0.18); border-color: rgba(0, 123, 255, 0.3); color: #b9ddff; }
    .streamlit-expanderHeader, .stExpander {
        background: rgba(10, 12, 18, 0.92) !important;
        border: 1px solid rgba(0, 255, 220, 0.12) !important;
    }
    .stDataFrame, .css-1lcbmhc.e1tzin5v2, .css-1e5imcs4 {
        background: rgba(8, 12, 18, 0.9) !important;
        color: #e6f7ff !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #00ffdd 0%, #0ae3ff 100%) !important;
        color: #07080f !important;
        border: none !important;
        box-shadow: 0 18px 35px rgba(0, 255, 220, 0.16);
    }
    .stButton>button:hover {
        opacity: 0.95 !important;
    }
    .stPlotlyChart > div {
        border-radius: 24px !important;
        background: #07080f !important;
        box-shadow: 0 0 40px rgba(0, 255, 220, 0.05) !important;
    }
    .app-title h1 {
        margin-top: 0.25rem;
        margin-bottom: 0.1rem;
        font-size: 1.6rem;
        line-height: 1.15;
        color: #ffffff;
    }
    .app-title p {
        margin-top: 0.25rem;
        color: #9fdfff;
        opacity: 0.9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# initialize session state keys used to track uploads and results
if "current_file" not in st.session_state:
    st.session_state.current_file = None
if "current_file_hash" not in st.session_state:
    st.session_state.current_file_hash = None
if "eda_output" not in st.session_state:
    st.session_state.eda_output = None
if "summary_text" not in st.session_state:
    st.session_state.summary_text = None
if "summary_data" not in st.session_state:
    st.session_state.summary_data = None
if "chart_paths" not in st.session_state:
    st.session_state.chart_paths = None
if "pipeline_completed" not in st.session_state:
    st.session_state.pipeline_completed = False
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "eval" not in st.session_state:
    st.session_state.eval = None


def clear_results_for_new_file() -> None:
    """Clear previous run artifacts from session state and reset pipeline statuses."""
    st.session_state.eda_output = None
    st.session_state.summary_text = None
    st.session_state.summary_data = None
    st.session_state.chart_paths = None
    st.session_state.pipeline_completed = False
    st.session_state.pipeline_result = None
    st.session_state.current_file_hash = None
    # reset pipeline statuses
    for agent in AGENT_ORDER:
        pipeline_statuses[agent] = "pending"

st.markdown(
    """
    <div class='app-title'>
        <h1>AI Business Analyst Agent</h1>
        <p>Upload a CSV in the sidebar and run the pipeline to explore data insights in a dark dashboard layout.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = None
saved_path = None
security_result = None
schema_df = None
can_run_pipeline = False
pipeline_completed = False
pipeline_statuses = st.session_state.get(
    "pipeline_statuses",
    {agent: "pending" for agent in AGENT_ORDER}
)
status_placeholders: dict = {}


def metric_card(label: str, value: str, note: str | None = None) -> str:
    note_html = f"<div class='card-note'>{note}</div>" if note else ""
    return f"""
    <div class='metric-card'>
        <div class='card-label'>{label}</div>
        <p class='card-value'>{value}</p>
        {note_html}
    </div>
    """


def render_status_table() -> None:
    """Render status badges and create st.empty placeholders for live updates."""
    global status_placeholders
    status_columns = st.columns(len(AGENT_ORDER), gap="small")
    # create placeholders once, then reuse for live updates
    if not status_placeholders:
        for col, agent in zip(status_columns, AGENT_ORDER):
            placeholder = col.empty()
            status_placeholders[agent] = placeholder
            status_html = STATUS_BADGES[pipeline_statuses[agent]]
            placeholder.markdown(f"**{agent}**<br>{status_html}", unsafe_allow_html=True)
    else:
        # ensure layout still rendered, then refresh existing placeholders
        for agent in AGENT_ORDER:
            placeholder = status_placeholders.get(agent)
            if placeholder:
                status_html = STATUS_BADGES[pipeline_statuses[agent]]
                placeholder.markdown(f"**{agent}**<br>{status_html}", unsafe_allow_html=True)


def update_status(agent: str, state: str) -> None:
    """Update internal status and immediately refresh the corresponding placeholder."""
    pipeline_statuses[agent] = state
    st.session_state["pipeline_statuses"] = pipeline_statuses.copy()
    placeholder = status_placeholders.get(agent)
    if placeholder:
        placeholder.markdown(f"**{agent}**<br>{STATUS_BADGES[state]}", unsafe_allow_html=True)

def human_error_message(agent: str, exc: Exception) -> str:
    text = str(exc).strip().lower()
    if agent == "Security":
        if "validation failed" in text or "blocked" in text:
            return "Security validation failed. The uploaded file did not pass security checks."
        return "Security validation failed due to an unexpected issue."
    if agent == "CSVReader":
        return "CSV reading failed. Please make sure the file is a valid CSV and try again."
    if agent == "EDA":
        return "EDA analysis failed. Please check the data format and try again."
    if agent == "ChartGenerator":
        return "Chart generation failed. The data may contain values that cannot be visualised."
    if agent == "ChartValidator":
        return "Chart validation failed. One or more chart checks did not pass."
    if agent == "Summary":
        return "Summary generation failed. Please try again later."
    return "The pipeline failed due to an unexpected error."


with st.sidebar:
    st.header("Upload & Controls")
    uploaded_file = st.file_uploader(
        "Drop CSV or click to browse",
        type=["csv"],
        help="Upload the dataset for the business analyst pipeline.",
    )
    run_pipeline_button = st.button("Run full pipeline")
    st.markdown("---")
    st.markdown(
        "<div style='color:#9edcff;font-size:0.95rem;'>Use the controls above to upload your CSV and execute the end-to-end agent flow.</div>",
        unsafe_allow_html=True,
    )

if uploaded_file:
    incoming_name = Path(uploaded_file.name).name
    incoming_bytes = uploaded_file.getvalue()
    incoming_hash = hashlib.sha256(incoming_bytes).hexdigest()

    # detect new or changed upload and reset stale session results
    if (
        st.session_state.current_file != incoming_name
        or st.session_state.current_file_hash != incoming_hash
    ):
        clear_results_for_new_file()
        st.session_state.current_file = incoming_name
        st.session_state.current_file_hash = incoming_hash
        schema_df = None

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_path = UPLOAD_DIR / incoming_name
    with saved_path.open("wb") as f:
        f.write(incoming_bytes)
    try:
        update_status("Security", "running")
        security_result = orchestrator.security_agent(str(saved_path))
        status = security_result.get("status")
        reason = security_result.get("reason", "unknown")
        if status == "PASSED":
            update_status("Security", "passed")
            can_run_pipeline = True
        elif status == "BLOCKED":
            update_status("Security", "blocked")
            for agent in AGENT_ORDER[1:]:  # skip Security, mark rest as skipped
                update_status(agent, "skipped")
            st.error(f"Pipeline blocked: {reason}")
            # show the pipeline status to indicate the block
            st.subheader("Pipeline status")
            render_status_table()
            can_run_pipeline = False
            st.stop()
        else:
            update_status("Security", "failed")
            st.error(f"Security validation failed: {reason}")
            can_run_pipeline = False
    except Exception as exc:  # pragma: no cover
        update_status("Security", "failed")
        security_result = {"status": "FAILED", "reason": str(exc)}
        can_run_pipeline = False

    try:
        df = pd.read_csv(saved_path)
        schema_df = pd.DataFrame({"column": df.columns, "dtype": df.dtypes.astype(str).values})
    except Exception:
        schema_df = None

row_count = "—"
col_count = "—"
validation_status = "Awaiting upload"
if saved_path and saved_path.exists():
    try:
        df_stats = pd.read_csv(saved_path)
        row_count = f"{len(df_stats):,}"
        col_count = f"{df_stats.shape[1]:,}"
    except Exception:
        row_count = "Unknown"
        col_count = "Unknown"

if security_result is None:
    validation_status = "Pending"
elif security_result.get("status") == "PASSED":
    validation_status = "Passed"
elif security_result.get("status") == "FAILED":
    validation_status = "Failed"

stats_cols = st.columns(3, gap="large")
stats_cols[0].markdown(metric_card("Rows", row_count, "Dataset size"), unsafe_allow_html=True)
stats_cols[1].markdown(metric_card("Columns", col_count, "Feature count"), unsafe_allow_html=True)
stats_cols[2].markdown(metric_card("Validation", validation_status, "Security check status"), unsafe_allow_html=True)

st.markdown("---")

with st.container():
    st.subheader("Pipeline status")
    render_status_table()

if run_pipeline_button and saved_path and security_result and security_result.get("status") == "PASSED":
    st.session_state["eval"] = None
    current_agent = "Security"
    progress_bar = st.progress(0)
    progress_message = st.empty()
    try:
        update_status("Security", "running")
        security_result = orchestrator.security_agent(str(saved_path))
        status = security_result.get("status")
        reason = security_result.get("reason", "unknown")
        if status == "PASSED":
            update_status("Security", "passed")
        elif status == "BLOCKED":
            update_status("Security", "blocked")
            for agent in AGENT_ORDER[1:]:  # skip Security, mark rest as skipped
                update_status(agent, "skipped")
            st.error(f"Pipeline blocked: {reason}")
            current_agent = "Security"
            st.stop()
        else:
            update_status("Security", "failed")
            progress_message.error("Security validation failed. The uploaded file did not pass security checks.")
            raise RuntimeError("Security validation failed")

        current_agent = "CSVReader"
        update_status("CSVReader", "running")
        progress_bar.progress(16)
        progress_message.info("Running CSVReaderAgent...")
        orchestrator.csv_reader_agent(str(saved_path))
        update_status("CSVReader", "passed")

        current_agent = "EDA"
        update_status("EDA", "running")
        progress_bar.progress(33)
        progress_message.info("Running EDAAnalyzerAgent...")
        df = pd.read_csv(saved_path)
        eda_output = orchestrator.eda_agent(df)
        st.session_state.eda_output = eda_output
        update_status("EDA", "passed")

        current_agent = "ChartGenerator"
        update_status("ChartGenerator", "running")
        progress_bar.progress(50)
        progress_message.info("Running ChartGeneratorAgent...")
        orchestrator.chart_agent(eda_output, df)
        update_status("ChartGenerator", "passed")

        current_agent = "ChartValidator"
        update_status("ChartValidator", "running")
        progress_bar.progress(66)
        progress_message.info("Running ChartValidatorAgent...")
        validation_result = orchestrator.chart_validator_agent(str(saved_path), eda_output, df)
        if validation_result.get("status") == "PASS":
            update_status("ChartValidator", "passed")
        else:
            update_status("ChartValidator", "failed")
            progress_message.error("Chart validation failed. One or more chart checks did not pass.")
            raise RuntimeError("Chart validation failed")

        current_agent = "Summary"
        update_status("Summary", "running")
        progress_bar.progress(83)
        progress_message.info("Running SummaryAgent...")
        orchestrator.summary_agent(eda_output, str(saved_path))
        update_status("Summary", "passed")

        # Load the pipeline summary JSON after successful summary generation.
        summary_data = None
        if OUTPUT_SUMMARY.exists():
            try:
                summary_data = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
                st.session_state.summary_data = summary_data
            except Exception as exc:  # pragma: no cover
                st.warning(f"Unable to load generated summary output: {exc}")

        st.session_state.pipeline_result = {
            "status": "PASS",
            "file_name": st.session_state.current_file,
            "file_hash": st.session_state.current_file_hash,
            "summary_data": summary_data,
            "eda": st.session_state.eda_output,
        }

        progress_bar.progress(100)
        progress_message.success("Pipeline completed successfully.")
        pipeline_completed = True
        st.session_state.pipeline_completed = True
        
        # Re-read fresh pipeline status from file and store in session state
        pipeline_status_path = PROJECT_ROOT / "outputs" / "pipeline_status.json"
        if pipeline_status_path.exists():
            try:
                status_data = json.loads(pipeline_status_path.read_text(encoding="utf-8"))
                st.session_state["pipeline_statuses"] = status_data
                # Load eval report after pipeline completion but before rerun
                eval_report_path = PROJECT_ROOT / "outputs" / "eval_report.json"
                if eval_report_path.exists():
                    try:
                        eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
                        st.session_state["eval"] = eval_report
                        # format display values for the UI
                        st.session_state["total_time"] = f"{eval_report['pipeline_duration_sec']:.1f}s"
                        st.session_state["slowest_agent"] = f"{eval_report['slowest_agent']} ({eval_report['slowest_agent_sec']:.1f}s)"
                        st.session_state["llm_accuracy"] = f"{eval_report['llm_accuracy_score']}%"
                        st.session_state["fallback_rate"] = f"{eval_report['llm_fallback_rate']}%"
                        st.session_state["retries"] = eval_report['chart_validation_retries']
                        st.session_state["security_status"] = eval_report['security_status']
                        st.session_state["total_tokens"] = f"{eval_report['total_llm_tokens']:,}"
                    except Exception as exc:  # pragma: no cover
                        st.warning(f"Unable to load evaluation report: {exc}")
                st.rerun()
            except Exception as exc:  # pragma: no cover
                st.warning(f"Unable to load pipeline status: {exc}")
    except Exception as exc:  # pragma: no cover
        progress_bar.progress(100)
        reason = exc.args[0] if hasattr(exc, "args") and exc.args else "an unexpected error occurred"
        progress_message.error(f"{current_agent} failed: {reason}. Please review the data and try again.")

st.markdown("---")

if schema_df is not None:
    with st.expander("Column Type Preview"):
        st.markdown("**Column type preview**")
        st.dataframe(schema_df, use_container_width=True)

# Raw data preview (first 50 rows)
if saved_path is not None and saved_path.exists():
    try:
        df_preview = pd.read_csv(saved_path, nrows=50)
        dtype_map = df_preview.dtypes.astype(str).to_dict()
        df_preview = df_preview.rename(columns={col: f"{col} ({dtype_map[col]})" for col in df_preview.columns})
        with st.expander("Raw Data Preview"):
            st.dataframe(df_preview, use_container_width=True)
    except Exception as exc:  # pragma: no cover
        st.warning(f"Unable to load raw data preview: {exc}")

summary_data = None
if OUTPUT_SUMMARY.exists():
    try:
        summary_data = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
        st.session_state.summary_data = summary_data
        # Do not display raw summary JSON to the user; keep chart paths if present
        if chart_paths := summary_data.get("charts"):
            st.session_state.chart_paths = chart_paths
    except Exception as exc:  # pragma: no cover
        st.warning(f"Unable to load summary output: {exc}")
    else:
        if (
            st.session_state.pipeline_result
            and st.session_state.pipeline_result.get("file_hash") == st.session_state.current_file_hash
            and isinstance(summary_data, dict)
        ):
            st.session_state.pipeline_result["summary_data"] = summary_data

# Plots expander (interactive histograms and heatmap)
if saved_path is not None and saved_path.exists():
    try:
        df_interactive = pd.read_csv(saved_path)
        numeric_cols = df_interactive.select_dtypes(include="number").columns.tolist()

        if numeric_cols:
            with st.expander("Plots"):
                st.subheader("Interactive Histograms")
                # render histograms in rows of two columns
                for i in range(0, len(numeric_cols), 2):
                    left_col_name = numeric_cols[i]
                    right_col_name = numeric_cols[i + 1] if (i + 1) < len(numeric_cols) else None
                    left, right = st.columns(2, gap="large")

                    fig_left = px.histogram(
                        df_interactive,
                        x=left_col_name,
                        nbins=30,
                        marginal="box",
                        opacity=0.8,
                        title=f"Histogram: {left_col_name}",
                        color_discrete_sequence=["#00ffd5"],
                        template="plotly_dark",
                    )
                    fig_left.update_layout(hovermode="x unified", paper_bgcolor="#07080f", plot_bgcolor="#07080f")
                    left.plotly_chart(fig_left, use_container_width=True)

                    if right_col_name:
                        fig_right = px.histogram(
                            df_interactive,
                            x=right_col_name,
                            nbins=30,
                            marginal="box",
                            opacity=0.8,
                            title=f"Histogram: {right_col_name}",
                            color_discrete_sequence=["#00ffd5"],
                            template="plotly_dark",
                        )
                        fig_right.update_layout(hovermode="x unified", paper_bgcolor="#07080f", plot_bgcolor="#07080f")
                        right.plotly_chart(fig_right, use_container_width=True)

                # after histograms, render correlation heatmap if available
                correlations = None
                if st.session_state.eda_output and isinstance(st.session_state.eda_output, dict):
                    correlations = st.session_state.eda_output.get("correlations")

                if correlations:
                    corr_df = pd.DataFrame(correlations)
                    left, right = st.columns(2, gap="large")
                    heatmap_fig = px.imshow(
                        corr_df,
                        text_auto=True,
                        aspect="auto",
                        color_continuous_scale="Tealrose",
                        title="Correlation Heatmap",
                        labels={"x": "Column", "y": "Column", "color": "Correlation"},
                        template="plotly_dark",
                    )
                    heatmap_fig.update_layout(paper_bgcolor="#07080f", plot_bgcolor="#07080f")
                    left.plotly_chart(heatmap_fig, use_container_width=True)
                else:
                    st.info("Correlation matrix is not available yet.")
        else:
            st.info("No numeric columns found for histogram generation.")
    except Exception as exc:  # pragma: no cover
        st.warning(f"Unable to render charts: {exc}")
else:
    st.write("Upload a CSV and run the pipeline to populate charts.")
    st.write("Charts will appear here in a two-column grid.")

pipeline_result_valid = (
    st.session_state.pipeline_result is not None
    and st.session_state.pipeline_result.get("status") == "PASS"
    and st.session_state.pipeline_result.get("file_name") == st.session_state.current_file
    and st.session_state.pipeline_result.get("file_hash") == st.session_state.current_file_hash
)

if pipeline_result_valid:
    pipeline_result_data = st.session_state.pipeline_result.get("summary_data")
    eda_summary = None
    if (
        isinstance(st.session_state.pipeline_result.get("eda"), dict)
        and st.session_state.pipeline_result["eda"].get("llm_summary")
    ):
        eda_summary = st.session_state.pipeline_result["eda"].get("llm_summary")
    elif isinstance(st.session_state.eda_output, dict):
        eda_summary = st.session_state.eda_output.get("llm_summary")
    elif isinstance(pipeline_result_data, dict):
        eda_summary = pipeline_result_data.get("eda", {}).get("llm_summary")

    with st.expander("EDA Conclusions"):
        eda_data = None
        if isinstance(st.session_state.eda_output, dict):
            eda_data = st.session_state.eda_output
        elif pipeline_result_valid and isinstance(st.session_state.pipeline_result.get("eda"), dict):
            eda_data = st.session_state.pipeline_result.get("eda")

        if eda_data is None:
            st.info("EDA output is not available yet.")
        else:
            stats = eda_data.get("stats", {})
            nulls = eda_data.get("nulls", {})
            correlations = eda_data.get("correlations", {})
            outliers = eda_data.get("outliers", {})

            shape_text = "Unknown"
            numeric_ranges = {}
            if saved_path is not None and saved_path.exists():
                try:
                    df_overview = pd.read_csv(saved_path)
                    shape_text = f"{df_overview.shape[0]:,} rows × {df_overview.shape[1]:,} columns"
                    numeric_cols = df_overview.select_dtypes(include="number").columns
                    for col in numeric_cols:
                        numeric_ranges[col] = {
                            "min": float(df_overview[col].min()),
                            "max": float(df_overview[col].max()),
                        }
                except Exception:
                    pass

            st.markdown("### Dataset Overview")
            st.markdown(f"**Shape:** {shape_text}")
            if nulls:
                st.markdown("**Null counts:**")
                for col, count in nulls.items():
                    st.markdown(f"- `{col}`: {count}")
            if numeric_ranges:
                range_rows = [
                    {"Column": col, "Min": rng["min"], "Max": rng["max"]}
                    for col, rng in numeric_ranges.items()
                ]
                st.dataframe(pd.DataFrame(range_rows), use_container_width=True)

            st.divider()
            st.markdown("### EDA Findings Per Column")
            if stats:
                eda_rows = [
                    {
                        "Column": col,
                        "Mean": stat_values.get("mean"),
                        "Std Dev": stat_values.get("std"),
                        "Skewness": stat_values.get("skew"),
                        "Kurtosis": stat_values.get("kurtosis"),
                    }
                    for col, stat_values in stats.items()
                ]
                st.dataframe(pd.DataFrame(eda_rows), use_container_width=True)
            else:
                st.markdown("No numeric column statistics available.")

            st.divider()
            st.markdown("### Outlier Summary")
            if outliers:
                for col, idxs in outliers.items():
                    skew = stats.get(col, {}).get("skew", 0) if stats else 0
                    tail = "right tail" if skew > 0 else "left tail"
                    st.markdown(f"`{col}`: {len(idxs)} outliers ({tail})")
            else:
                st.markdown("No outliers detected.")

            st.divider()
            st.markdown("### Correlation Summary")
            if correlations:
                try:
                    corr_df = pd.DataFrame(correlations)
                    abs_corr = corr_df.abs()
                    cols = list(corr_df.columns)
                    related_pairs = []
                    for i, col1 in enumerate(cols):
                        for col2 in cols[i + 1:]:
                            if abs_corr.loc[col1, col2] >= 0.7:
                                related_pairs.append((col1, col2))
                    if related_pairs:
                        pair_names = ", ".join([f"`{a}` & `{b}`" for a, b in related_pairs])
                        st.markdown(f"Strong relationships found: {pair_names}.")
                    else:
                        st.markdown("Columns are mostly independent.")
                except Exception:
                    st.markdown("Correlation data incomplete.")
            else:
                st.markdown("Correlation data not available.")

            st.divider()
            st.markdown("### Key Takeaways")
            st.markdown(f"- Dataset: {shape_text}")
            if outliers:
                st.markdown(f"- Outliers found in {len(outliers)} column(s).")
            else:
                st.markdown("- No data quality issues from outliers.")
            st.markdown("- Review numeric ranges and correlations for analysis.")

    with st.expander("Summary Report"):
        if SUMMARY_MD.exists():
            summary_text = SUMMARY_MD.read_text(encoding="utf-8")
            st.markdown(summary_text)
            st.download_button(
                label="Download summary.md",
                data=summary_text,
                file_name="summary.md",
                mime="text/markdown",
            )
        else:
            st.info("Summary report is not available yet.")

with st.expander("View audit log"):
    if AUDIT_LOG.exists():
        st.text(AUDIT_LOG.read_text(encoding="utf-8"))
    else:
        st.write("No audit log found yet.")
