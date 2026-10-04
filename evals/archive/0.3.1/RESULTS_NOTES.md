# Notes on the v0.3.1 results

These notes explain [RESULTS.md](RESULTS.md). Every run file is in `evals/runs/`. `evals/tally_runs.py` reproduces the failure breakdown, and `evals/compare_residuals.py` reproduces the residual diagnosis.

## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5 |
| Skill commit | bea3d11 (skill frozen for the whole batch) |
| Rubric / schema | 0.2.0 / 0.4.0 |
| Cases | the same 13 cases as the v0.3.0 baseline |
| Runs per case | 5 (65 runs), API default temperature |
| Output limit | 64,000 tokens for every run |
| Batch window | 2026-10-03, starting 05:01 UTC |

## Compared with the v0.3.0 baseline

| Measure | v0.3.0 | v0.3.1 |
|---|---|---|
| Validator clean | 77% | 91% |
| Mean recall | 92% | 92% |
| Failures from references to data stores | 5 runs | 0 |
| Failures from references to planned capabilities | 3 runs | 0 |
| Case 02 (clean) false positives | 1 | 0 |
| Mean output tokens | 25,836 | 29,612 |

v0.3.1 targeted the schema and validator gaps the baseline exposed, and those failures are gone. Recall held steady. Output grew about 15 percent, consistent with runs now declaring stores, peers, and planned items.

## Why 6 runs were not validator clean

| Cause | Runs | Cases | Kind |
|---|---|---|---|
| Element linked to the protocol peer that shares its id | 2 | 05 | Validator bug introduced in v0.3.1: the self reference rule did not allow this legitimate link |
| `severs_path` on a control that does not qualify | 2 | 04, 13 | Model error, caught as designed; also seen in the baseline |
| `"forecast": null` instead of omitting the field | 1 | 08 | Model error |
| Malformed JSON | 1 | 09 | Model error, likely an unescaped quote in evidence quoting the hostile artifact text |

As with the baseline, the validator was not changed and the runs were not rescored. The validator bug and guidance for the two model errors ship in v0.3.2.

The one malformed run is most of the drop in case 09 recall (90 percent to 70 percent): it scores zero, and the other four runs match the baseline.

## Residual agreement: what the diagnosis found

Rollup residual agreement fell in five cases even though the rubric did not change (01, 03, 04, 10, and 11, each to 60 or 80 percent). `compare_residuals.py` examined the main attack path finding in every run of those cases.

1. **No run rated residual below what the rubric credits allow.** All 25 main path findings were at or above the floor computed from the controls on the path. The model is not giving credit the rubric withholds.
2. **The hypothesis that new reference options caused it was wrong.** Controls covering only elements or peers appeared six times, and every one was a recommended control that earns no credit.
3. **Most of the drop is the rollup, not the main path.** The rating rollup takes the worst finding. Runs report different secondary findings, so the rollup moves even when the main path does not. Main path residual agreement was 100 percent in cases 01, 10, and 11.
4. **The rest is unstated judgment above the floor.** Five of the 25 runs rated the main path above the floor without saying why: three in case 03 and two in case 04. In case 04 that judgment was arguably right, because the design's "always allow after first approval" means later calls are never reviewed, which the rubric did not express.
5. **One run wired an approval gate differently** (in `covers` rather than `approval_gate_ref`), which earns different credit.

Main path residual agreement:

| Case | Rollup agreement | Main path agreement |
|---|---|---|
| 01 | 80% | 100% |
| 03 | 60% | 80% |
| 04 | 60% | 60% |
| 10 | 60% | 100% |
| 11 | 60% | 100% |

## Known limitations shown by this batch

1. **Approval gates under high volume are still overcredited.** In case 10, every run rated the main path `moderate`, exactly the rubric floor, and the real incident proves the gate failed. This is unchanged from the baseline and needs the approval volume factor planned for v0.4.0.
2. **Missing property risks are still rated outside the expected range** (case 13), as in the baseline. Planned for v0.4.0.
3. **Residual can exceed the floor without a stated reason**, which lowers agreement. Fixed in v0.3.2.

## What is next

- **v0.3.2:**
  - fixes the validator bug
  - requires `residual_rationale` whenever residual is above the floor
  - treats remembered approvals as non gates
  - requires every approval gate to be wired through `approval_gate_ref`
  - adds guidance on null fields and quoting
  - adds a main path residual metric to the report
- **v0.4.0:** STRIDE per element coverage, tiering for missing property findings, the approval volume factor, and entry plus impact tagging, measured with held out cases.
