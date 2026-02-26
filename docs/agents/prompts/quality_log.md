
## 2026-02-25 — archivist
Model: deepseek/deepseek-r1
Confidence: high
Weaknesses identified:
  - Output format instruction appears after empty JSON template, risking prose additions
  - Missing concrete example with real values for model imitation
  - No explicit prohibition against explanatory text outside JSON
Changes:
  - Added explicit 'ONLY JSON' prohibition first in output section [CHANGE: prevents prose leakage]
  - Included filled example with realistic violation data [CHANGE: better few-shot guidance]
  - Added negative instruction 'DO NOT COPY EXAMPLE VALUES' [CHANGE: prevents placeholder replication]
