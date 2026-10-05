# Notes on the v0.3.2 batch (not released)

v0.3.2 was measured but not released, because this batch showed it forecast fewer findings than v0.3.1. The results are kept here so the regression and its fix stay on the record. [RESULTS.md](RESULTS.md) has the table, and `runs/` has every run.

## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5 |
| Skill commit | cf0ea36 (skill frozen for the whole batch) |
| Rubric / schema | 0.2.1 / 0.5.0 |
| Cases | the same 13 cases as v0.3.0 and v0.3.1 |
| Runs per case | 5 (65 runs), output limit 64,000 tokens |
| Batch date | 2026-10-04 |

## What v0.3.2 fixed

| Measure | v0.3.1 | v0.3.2 |
|---|---|---|
| Validator clean | 91% | 95% |
| Mean recall | 92% | 91% |
| Case 04 residual in range | 40% | 100% |
| Case 05 validator clean | 60% | 100% |
| Main path residual agreement, lowest case | 60% | 80% |

- **The remembered approval rule worked.** Case 04 rated the main path critical in every run, because "always allow after first approval" no longer earns credit.
- **Residual rationales worked.** All nine runs that rated a main path above the rubric floor explained why. In the GitHub and Supabase MCP backtests, eight of ten runs did so, citing collapsed arguments, model written summaries, per call review that cannot see the whole sequence, and approval volume. That independently matches how the real incidents failed.

## Why it was not released

Share of present findings with a forecast block:

| Case | v0.3.1 | v0.3.2 |
|---|---|---|
| 01 | 100% | 88% |
| 02 | 83% | 67% |
| 03 | 95% | 68% |
| 04 | 80% | 25% |
| 05 | 64% | 69% |
| 06 | 100% | 86% |
| 07 | 60% | 22% |
| 08 | 0% | 0% |
| 09 | 33% | 18% |
| 10 | 78% | 100% |
| 11 | 78% | 70% |
| 12 | 93% | 71% |
| 13 | 67% | 0% |
| **All** | **76% (98 of 129)** | **55% (72 of 130)** |

The cause was new guidance in v0.3.2. To illustrate omitting empty fields, it said to leave out `forecast` rather than set it to `null`, and runs read that as permission to skip forecasts. The case level forecast rating is filled in separately, so the report still showed forecasts in range and hid the drop. Case 13 recall fell from 87 to 67 percent because no run produced the forecast trigger the case checks.

The table also shows an older gap: even v0.3.1 forecast only 76 percent of findings, because nothing required a forecast.

## Other failures

Three of 65 runs were not validator clean, each a single model error: an accepted risk with no approver (case 08), malformed JSON (case 08), and an element linked to a container image name instead of an id (case 10).

## Fixed in v0.3.3

- Every finding must have a forecast; the validator rejects any finding without one.
- A forecast that changes nothing is valid and expected: list the triggers considered and set `projected_risk` equal to `residual_risk`.
- The guidance example that caused the drop now uses `residual_rationale`.
