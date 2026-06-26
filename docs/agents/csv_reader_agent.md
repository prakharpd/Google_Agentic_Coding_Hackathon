# CSVReaderAgent

## Role
Load and profile CSV after security clearance.

## Model
`gpt-oss:20b-cloud` via Ollama

## Responsibilities
1. Read CSV with pandas (auto encoding detection)
2. Return schema: columns, dtypes, null counts, shape
3. Generate ydata-profiling HTML report

## Input / Output
- Input: `filepath: str`
- Output: `{ "shape": [], "columns": [], "dtypes": {}, "null_counts": {}, "profile_path": "outputs/profile.html" }`

## Vibe Code Prompt
```
Using gpt-oss:20b-cloud via Ollama and Google ADK, create src/agents/csv_reader_agent.py.
- Load CSV using pandas with chardet encoding detection
- Extract schema: columns, dtypes, null counts, shape
- Run ydata-profiling ProfileReport → save to outputs/profile.html
- Return structured dict as above
```
