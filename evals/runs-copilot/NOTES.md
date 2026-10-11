# GitHub Copilot install check (v0.3.4)

This is an install verification, not an eval batch: one run on each of two cases, to confirm the skill works when installed the way the README describes for Copilot. [RESULTS.md](RESULTS.md) has the scores.

## Setup

| Setting | Value |
|---|---|
| Platform | GitHub Copilot in VS Code, Agent mode |
| Model | Claude Opus 5.5, selected in Copilot |
| Skill | v0.3.4, copied unchanged to `.github/skills/para/` in a scratch repository |
| Cases | 01 support triage and 10 GitHub MCP backtest, given as files with the evaluator notes stripped, exactly as the eval harness presents them |
| Prompt | "Assess the risk of the agent design in <case>.md. Save the assessment JSON as <case>.assessment.json, validate it, and show me the report." A new chat for each case. |

## What happened

| Check | Result |
|---|---|
| Copilot discovered and loaded the PARA skill from `.github/skills/` | Yes |
| It ran `scripts/validate.py` rather than falling back to the checklist | Yes |
| It saved the assessment JSON | Yes |
| Both assessments validator clean | Yes |

Scores: case 01 recall 75 percent with all three tiers in range; case 10 recall 100 percent with inherent and forecast in range. Case 10's residual was out of range, the same known limitation every batch shows: the rubric gives the approval prompt too much credit.

## What this does and does not show

It shows the Copilot install path in the README works end to end: discovery, script execution, and valid output, with no changes to the skill.

It does not measure Copilot as a separate model family. Copilot ran a Claude model here, and one run per case is too few for agreement numbers. A follow up with a non Claude model selected in Copilot would cover a second model on the same platform.
