# Notes on the v0.3.3 results

These notes explain [RESULTS.md](RESULTS.md). Every run file is in `evals/runs/`. `evals/tally_runs.py` reproduces the failure breakdown, and `evals/compare_residuals.py` the residual diagnosis.

## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5 |
| Skill commit | 03d507d (skill frozen for the whole batch) |
| Rubric / schema | 0.2.2 / 0.5.0 |
| Cases | the same 13 cases as every earlier batch |
| Runs per case | 5 (65 runs), output limit 64,000 tokens |
| Batch date | 2026-10-05 |

## Across all batches

| Measure | v0.3.0 | v0.3.1 | v0.3.2 (not released) | v0.3.3 |
|---|---|---|---|---|
| Validator clean | 77% | 91% | 95% | 95% |
| Mean recall | 92% | 92% | 91% | **96%** |
| Findings with a forecast | not measured | 76% | 55% | **100%** |
| Case 04 residual in range | 0% | 40% | 100% | 100% |
| Case 13 recall | 87% | 87% | 67% | **100%** |
| Lowest main path residual agreement | not measured | 60% | 80% | 80% |
| Mean output tokens | 25,836 | 29,612 | 27,406 | 29,264 |

v0.3.3 restored forecasting after the v0.3.2 regression and went further: every one of 134 present findings carries a forecast, because the validator now requires one. Recall reached its highest level. Everything v0.3.2 fixed held: case 04 rated in range on every run, and main path residual agreement stayed at 80 percent or higher in every case that has a main path.

## Backtests

For both reconstructed public incidents, every run rated inherent risk critical, the expected tier. Recall was 100 percent on the GitHub MCP toxic agent flow (May 2025) and 88 percent on the Supabase MCP support ticket injection (July 2025).

## Why 3 runs were not validator clean

| Cause | Run | Kind |
|---|---|---|
| `severs_path` on a control that does not qualify | case 02 | Model error. It has appeared in every batch since v0.3.0, so the guidance needs work |
| Element linked to a configuration path instead of an id | case 11 | Model error, also seen in v0.3.2 |
| Residual rated above inherent | case 12 | Model error, caught as designed |

## Known limitations shown by this batch

1. **False positives on the forecast only design rose.** Case 08 has no complete attack path today, so any present finding at `moderate` or above counts as a false positive. Three of five runs reported one, compared with one run in v0.3.1 and v0.3.2 and none in v0.3.0. The clean case (02) had one. Whether requiring a forecast on every finding encourages extra present findings is an open question for v0.4.0.
2. **Approval gates under high volume are still overcredited by the rubric.** The model now compensates with stated rationales in the backtests, but the rubric itself still floors those gates too low. The approval volume factor in the v0.4.0 design addresses this.
3. **Missing property risks are rated outside the expected range** (case 13, inherent and residual). Detection is complete (100 percent recall); tiering is planned for v0.4.0.
4. **Rollup residual agreement is lower than main path agreement** in cases 01 and 03 (60 percent), because runs report different secondary findings. Main path agreement in both is 100 percent.

## What is next

v0.4.0, per `design/0.4.0-stride-coverage.md`, measured against this batch with held out cases:
- STRIDE per element coverage
- tiering for missing property findings
- the approval volume factor
- containment credit that requires constraining the sink
- entry plus impact tagging
- clearer `severs_path` guidance
