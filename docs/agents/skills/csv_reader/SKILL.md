---
name: CSVReaderAgent
description: Load and profile CSV files (schema extraction and optional HTML profiling) after security clearance.
triggers:
  positive:
    - file.cleared.by_security
    - user.request.schema
  negative:
    - unreadable.encoding
    - unsupported.filetype
    - missing.file
tier: read-only
---

## Objective

Safely load a CSV into a pandas DataFrame, extract schema (columns, dtypes, null counts, shape), and generate an HTML profiling report when available.

## Input/Output Contract

- Input: `filepath: str`
- Output: `{ "shape": [rows, cols], "columns": [...], "dtypes": {...}, "null_counts": {...}, "profile_path": str | null }`

## Step-by-step Workflow

1. Receive a `filepath` and confirm it exists.
2. Detect encoding via `src/tools/file_reader.py::detect_encoding` and load CSV with `load_csv`.
3. Extract `shape`, `columns`, `dtypes`, and `null_counts` from the DataFrame.
4. Attempt to generate a profiling report (Sweetviz) and save to `outputs/profile.html` when the dependency is available.
5. Return the result dict and log events.

## Guardrails

- Do not call LLMs; work is deterministic and read-only.
- If profiling dependency is missing, return `profile_path: null` and log notice.
- Avoid loading extremely large files into memory (upstream security should have enforced size limits).

## References

- Specification: [docs/agents/csv_reader_agent.md](docs/agents/csv_reader_agent.md)
- Implementation: [src/agents/csv_reader_agent.py](src/agents/csv_reader_agent.py)
- File helpers: [src/tools/file_reader.py](src/tools/file_reader.py)
