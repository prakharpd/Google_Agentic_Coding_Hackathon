"""Integration test for the full Business Analyst Agent pipeline.

The test generates a small CSV file (already present in ``data/sample.csv``),
invokes the orchestrator with the ``--input`` argument and verifies that a
summary JSON file is produced containing the expected sections.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import unittest

# Import the orchestrator module from the src package
from src.agents import orchestrator


class TestFullPipeline(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure a clean state before each test run
        self.project_root = Path(__file__).resolve().parents[1]
        self.sample_csv = self.project_root / "data" / "sample.csv"
        self.summary_path = self.project_root / "outputs" / "summary.json"
        # Remove any previous summary file
        if self.summary_path.is_file():
            self.summary_path.unlink()

    def test_pipeline_completes_and_produces_summary(self) -> None:
        # Simulate command‑line arguments for the orchestrator
        sys.argv = ["orchestrator.py", "--input", str(self.sample_csv)]
        # Run the pipeline – it will raise SystemExit on failure which will fail the test
        orchestrator.main()

        # Verify that the summary JSON was written
        self.assertTrue(self.summary_path.is_file(), "Summary file was not created")
        summary = json.loads(self.summary_path.read_text())

        # Expected top‑level keys
        for key in ("security", "csv_reader", "eda", "charts"):
            self.assertIn(key, summary, f"Missing '{key}' in summary")

        # The charts section should contain at least one chart path
        self.assertIsInstance(summary["charts"].get("charts"), list)
        self.assertGreater(len(summary["charts"]["charts"]), 0, "No charts were generated")


if __name__ == "__main__":
    unittest.main()
