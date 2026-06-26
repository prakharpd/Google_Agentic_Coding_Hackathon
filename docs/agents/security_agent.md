# SecurityValidatorAgent

## Role
First gatekeeper. Runs before any LLM call.

## Model
`gpt-oss:20b-cloud` via Ollama

## Responsibilities
1. Scan CSV headers + string values for prompt injection
2. Validate schema (shape, dtypes, size)
3. Detect data poisoning
4. Write audit log

## Input / Output
- Input: `filepath: str`
- Output: `{ "status": "PASSED"|"BLOCKED", "reason": "...", "rows": int, "cols": int }`

## Vibe Code Prompt
```
Using gpt-oss:20b-cloud via Ollama and Google ADK, create src/agents/security_agent.py.
- Scan CSV column headers and string cells for prompt injection via regex
- Validate min 2 columns, non-empty, file size < 50MB
- Log result to audit.log with timestamp
- Return: {status, reason, rows, cols}
- Patterns to block: in docs/security.md
```
