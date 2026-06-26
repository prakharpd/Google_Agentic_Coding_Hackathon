"""Orchestrator for the Business Analyst Agent pipeline.

The orchestrator wires the four agents in the required order:

1. ``SecurityValidatorAgent`` – validates the CSV and returns a status.
2. ``CSVReaderAgent`` – loads the CSV and produces a profiling report.
3. ``EDAAnalyzerAgent`` – performs exploratory data analysis on the DataFrame.
4. ``ChartGeneratorAgent`` – creates visualisations based on the EDA output.

If the security step returns ``BLOCKED`` the pipeline stops immediately and a
log entry is written.  The script accepts the CSV path via a ``--input`` command‑
line argument.

Although the original specification mentions *Google ADK*, the actual ADK
library is not required for the orchestrator logic – we simply import the
agent modules that have been generated in ``src/agents``.  This keeps the code
portable and functional in the current environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Import the agents that have been implemented in this repository
from .security_agent import run_agent as security_agent
from .csv_reader_agent import run_agent as csv_reader_agent
from .eda_agent import run_agent as eda_agent
from .chart_agent import run_agent as chart_agent
from . import eda_agent as eda_agent_module
from . import chart_agent as chart_agent_module
from . import summary_agent as summary_agent_module
from .chart_validator_agent import validate_and_retry as chart_validator_agent
from .summary_agent import run_agent as summary_agent
from src.agents.eval_agent import run_agent as eval_agent

from ..utils.logger import log_info, log_error

__all__ = ["main"]


def write_pipeline_status(agent_name: str, status: str) -> None:
    """Write current pipeline status to outputs/pipeline_status.json."""
    status_file = Path("outputs/pipeline_status.json")
    status_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize or load existing status
    if status_file.exists():
        try:
            pipeline_status = json.loads(status_file.read_text())
        except Exception:
            pipeline_status = {}
    else:
        pipeline_status = {}
    
    # Update agent status
    pipeline_status[agent_name] = status
    
    # Write updated status to file
    status_file.write_text(json.dumps(pipeline_status, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Business Analyst Agent pipeline")
    parser.add_argument("--input", required=True, help="Path to the CSV file to analyse")
    args = parser.parse_args()

    csv_path = Path(args.input).resolve()
    if not csv_path.is_file():
        log_error(f"Input file does not exist: {csv_path}")
        sys.exit(1)

    # Initialize LLM call log for tracking
    llm_call_log = []

    # ---------------------------------------------------------------------
    # 1. Security validation
    # ---------------------------------------------------------------------
    log_info(f"Running SecurityValidatorAgent on {csv_path}")
    write_pipeline_status("Security", "running")
    security_result = security_agent(str(csv_path))
    if security_result.get("status") != "PASSED":
        log_error(
            f"Security validation BLOCKED – reason: {security_result.get('reason', 'unknown')}"
        )
        write_pipeline_status("Security", "blocked")
        sys.exit(1)
    log_info("Security validation PASSED")
    write_pipeline_status("Security", "passed")

    # ---------------------------------------------------------------------
    # 2. CSV reading / profiling
    # ---------------------------------------------------------------------
    log_info("Running CSVReaderAgent")
    write_pipeline_status("CSVReader", "running")
    csv_reader_output = csv_reader_agent(str(csv_path))
    # The CSVReaderAgent returns a dict with schema information and a profile path.
    # Load the CSV into a DataFrame for the next step.
    try:
        import pandas as pd

        df = pd.read_csv(csv_path)
    except Exception as exc:  # pragma: no cover – defensive
        log_error(f"Failed to load CSV for EDA: {exc}")
        write_pipeline_status("CSVReader", "failed")
        sys.exit(1)
    write_pipeline_status("CSVReader", "passed")

    # ---------------------------------------------------------------------
    # 3. EDA analysis
    # ---------------------------------------------------------------------
    log_info("Running EDAAnalyzerAgent")
    write_pipeline_status("EDA", "running")
    eda_output = eda_agent(df)
    write_pipeline_status("EDA", "passed")

    # ---------------------------------------------------------------------
    # 4. Chart generation
    # ---------------------------------------------------------------------
    log_info("Running ChartGeneratorAgent")
    write_pipeline_status("ChartGenerator", "running")
    chart_output = chart_agent(eda_output, df)
    write_pipeline_status("ChartGenerator", "passed")

    # ---------------------------------------------------------------------
    # 5. Chart validation
    # ---------------------------------------------------------------------
    log_info("Running ChartValidatorAgent")
    write_pipeline_status("ChartValidator", "running")
    validation_result = chart_validator_agent(str(csv_path), eda_output, df)
    if validation_result.get("status") != "PASS":
        log_error("Chart validation failed; SummaryAgent will not run")
        write_pipeline_status("ChartValidator", "failed")
        sys.exit(1)
    log_info("Chart validation PASSED")
    write_pipeline_status("ChartValidator", "passed")

    # ---------------------------------------------------------------------
    # 6. Summary generation
    # ---------------------------------------------------------------------
    log_info("Running SummaryAgent")
    write_pipeline_status("Summary", "running")
    summary_agent(eda_output, str(csv_path))
    write_pipeline_status("Summary", "passed")

    # Summarise results – write a small JSON summary to the workspace root.
    summary_path = Path("outputs/summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "security": security_result,
        "csv_reader": csv_reader_output,
        "eda": eda_output,
        "charts": chart_output,
        "validation": validation_result,
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    log_info(f"Pipeline complete – summary written to {summary_path}")
    log_info("Running EvalAgent")
    # Collect LLM call logs from agent modules (if present)
    combined_log = []
    try:
        combined_log.extend(eda_agent_module.LLM_CALL_LOG)
    except Exception:
        pass
    try:
        combined_log.extend(chart_agent_module.LLM_CALL_LOG)
    except Exception:
        pass
    try:
        combined_log.extend(summary_agent_module.LLM_CALL_LOG)
    except Exception:
        pass

    eval_agent(
        csv_filepath=str(csv_path),
        audit_log_path="audit.log",
        llm_call_log=combined_log,
    )


if __name__ == "__main__":
    main()
# orchestrator.py — scaffold via VS Code Agent Chat using prompt in docs/agents/orchestrator.md
