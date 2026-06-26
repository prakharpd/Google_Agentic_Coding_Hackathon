# Security Layer

## Threats Covered
| Threat | Mitigation |
|--------|-----------|
| Prompt Injection | Regex scan on CSV headers + string values |
| Data Poisoning | Schema validation, dtype checks, row limits |
| Audit Trail | Every file logged to audit.log with timestamp |

## Injection Patterns Blocked
```python
INJECTION_PATTERNS = [
    r"ignore previous", r"system prompt", r"<script",
    r"DROP TABLE", r"__import__", r"os\.system", r"eval\(", r"exec\("
]
```

## Validation Rules
- Minimum 2 columns required
- No empty DataFrames
- File size limit: 50MB

## Fail-Safe
If SecurityValidatorAgent returns BLOCKED → orchestrator halts entire pipeline. No data reaches LLM.
