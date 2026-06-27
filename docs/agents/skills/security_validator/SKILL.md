---
name: SecurityValidatorAgent
description: Deterministic CSV security and schema gate that blocks malicious or malformed files before any LLM call.
triggers:
  positive:
    - file.upload.csv
    - pipeline.start
    - user.request.security_check
  negative:
    - file.size_over_50MB
    - unsupported.filetype
    - known_poisoning_patterns
tier: read-only
---

## Objective

Run a deterministic safety gate on incoming CSV files to detect prompt injection, schema anomalies, data poisoning, and size limits before any LLM is invoked.

## Input/Output Contract

- Input: `filepath: str`
- Output: `{ "status": "PASSED" | "BLOCKED", "reason": str, "rows": int, "cols": int }`

## Step-by-step Workflow

1. Receive `filepath` for candidate CSV.
2. Normalize and resolve the path; log start to audit.
3. Run deterministic validators from `src/tools/security.py::validate_csv`:
   - header and cell regex checks for prompt-injection patterns
   - file size and row/column count checks
   - basic schema expectations (min columns, non-empty)
4. On PASS: read rows/cols for telemetry, write audit log entry.
5. On BLOCKED: write audit log with reason and abort downstream steps.

## Guardrails

- No LLM calls: this skill must be deterministic and read-only.
- Do not allow blocked files to proceed to other agents; always return `BLOCKED` with an explicit `reason`.
- Keep logs minimal and avoid writing any sensitive cell values into shared logs.

## References

- Specification: [docs/agents/security_agent.md](docs/agents/security_agent.md)
- Implementation: [src/agents/security_agent.py](src/agents/security_agent.py)
- Security helpers: [src/tools/security.py](src/tools/security.py)
