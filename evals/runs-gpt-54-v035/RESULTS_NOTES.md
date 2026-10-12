# Notes on the GPT-5.4 results (v0.3.5)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder. The v0.3.4 GPT-5.4 batch it is compared with is in [evals/runs-gpt-54](../runs-gpt-54/), and the Claude batch on the same commit is in [evals/runs-claude-v035](../runs-claude-v035/).

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard, Microsoft Foundry v1 API |
| Skill commit | efd367e (skill frozen for the whole batch) |
| Rubric / schema | 0.2.2 / 0.5.0 (unchanged from v0.3.4; schema field descriptions clarified) |
| Cases | the same 13 cases as every batch |
| Runs per case | 5 (65 runs), API default temperature and reasoning effort, output limit 64,000 tokens |
| Batch date | 2026-10-11 |
| Cost | $4.80 total, about $0.074 per assessment, at Azure list prices |

## What v0.3.5 changed

v0.3.5 targeted the two weaknesses the v0.3.4 GPT-5.4 batch exposed, without changing the rubric:
1. **Schema vocabulary.** Field descriptions, skill guidance, and validator hints now spell out the allowed values that runs had confused.
2. **Missing controls.** Every structural recommendation must be recorded as a `missing_recommended` control on the path, and the validator warns when one is missing.

## Compared with v0.3.4

| Measure | v0.3.4 | v0.3.5 |
|---|---|---|
| Validator clean | 92% | 98% |
| Failures from vocabulary confusion | 5 runs | 0 |
| Mean recall | 93% | 93% |
| Missing controls recorded per run, mean across cases | 1.6 | 3.2 |
| Main path residual agreement, case 04 | 60% | 100% |
| Main path residual agreement, case 07 | 40% | 60% |
| Main path residual agreement, case 09 | 80% | 100% |
| Main path residual agreement, case 11 | 100% | 80% |
| Runs with a false positive | 0 | 1 (case 08) |
| Mean output tokens per assessment | 4,391 | 4,413 |

Both fixes worked. The vocabulary failures are gone, and the number of missing controls recorded doubled, moving most of the way toward Claude's (4.5 per run in its v0.3.5 batch). Consistency improved where the fix was aimed: case 04 went from 60 to 100 percent main path agreement, case 07 from 40 to 60, and case 09 from 80 to 100. Case 11 dipped from 100 to 80 percent. Recall held steady.

## Why 1 run was not validator clean

One run in case 03 wrote a capability without its required `action` field, along with two other structural errors in the same document. It is a single model error, unrelated to either fix.

## Weaker cases

- **Case 12 (repudiation):** every run rated the forecast `moderate`, where `high` or `critical` is expected, and recall stayed at 67 percent. Rating risks that come from a missing property, like no attributable audit trail, is planned for v0.4.0.
- **Case 10 (GitHub MCP backtest):** main path agreement stayed at 60 percent. Runs split between the rubric floor for the approval prompt (`moderate`) and a stated judgment that the prompt is weaker (`high`). Claude shows the same split. The approval volume factor in v0.4.0 addresses it.
- **Case 07:** two runs rated the main path residual `low`, which only happens when a run credits a control as severing the path. Worth reviewing during v0.4.0 work.
- **Case 13** is rated outside the expected range, as on every batch and both models.
