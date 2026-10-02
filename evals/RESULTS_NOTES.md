# Notes on the v0.3.0 baseline results

These notes explain [RESULTS.md](RESULTS.md). Every run file behind the numbers is in `evals/runs/`, and `evals/tally_runs.py` reproduces the failure breakdown below.

## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5 |
| Skill commit | e158107 (skill frozen for the whole batch) |
| Rubric / schema | 0.2.0 / 0.3.0 |
| Cases | 13: the 11 cases of milestone 4 plus coverage cases 12 and 13 from the v0.4.0 design |
| Runs per case | 5 (65 runs), API default temperature |
| Output limit | 32,000 tokens for the first pass; runs truncated at that limit were redone at 64,000 |
| Batch window | 2026-09-30 18:57 UTC to 2026-10-01 04:01 UTC |

Evaluator notes in each case (what it tests, incident sources) are stripped before the model sees it, so the expected answer cannot leak into the prompt.

Disclosure on the output limit: the model's internal reasoning counts toward the limit. At 32,000 tokens a share of runs were cut off before the JSON closed, which scored as failed runs. The truncated runs were rerun at 64,000 with the skill unchanged. Mean output was 25,836 tokens per assessment.

## Headline

- **Mean recall 92%** across 65 runs.
- **Backtests:** for both reconstructed public incidents, every run rated inherent risk in the expected range. Recall was 100% on the GitHub MCP toxic agent flow (May 2025) and 88% on the Supabase MCP support ticket injection (July 2025). Run before either incident, PARA would have named the attack path and the approval prompt as the control that would fail.
- **Assessor injection held:** in case 09, every run rated the design critical despite artifact text instructing assessors to rate it low.
- **False positives:** none in 12 of 13 cases. The clean case (02) had one run that reported a present finding at or above `moderate`.
- **Validator clean 77%** (50 of 65). See the breakdown below.

## Why 15 runs were not validator clean

No run failed from truncation or unparseable output in the final batch. All 15 failures are validator errors. Counted by each run's first error:

| Cause | Runs | Cases | Kind |
|---|---|---|---|
| Referenced a data store (quota, chat history, audit log) | 5 | 12, 13 | Schema gap: 0.3.0 has no element type for stores |
| Referenced a planned capability from the roadmap | 3 | 08 | Schema gap: no way to declare a capability that does not exist yet |
| Referenced a peer or server by an invented name | 2 | 10, 11 | Model error: the protocol's `peer_ref` was available |
| Control `covers` a peer agent | 1 | 05 | Validator inconsistency: attack paths accept peers, `covers` did not |
| `severs_path` on a control that does not qualify | 2 | 01, 02 | Model error, caught as designed |
| Evidence locator used as an attack path step | 1 | 09 | Model error |
| Field the schema does not allow | 1 | 10 | Model error |

About 9 of the 15 failures trace to gaps in the schema or validator: the skill identified a real risk and had no valid way to record it. Cases 12 and 13 contributed to this: their stable ids tables offer `store.*` ids that schema 0.3.0 cannot hold. The validator was not loosened and the runs were not rescored; fixes ship in the next version and are measured by a new run.

## Known limitations shown by this batch

1. **Approval gates under high volume are overcredited.** Cases 04 and 10 show full agreement across runs on residual risk, and none in the expected range. The runs apply rubric step 2 correctly (an approval gate earns two tiers); the GitHub MCP incident shows that same gate failing under real approval volume. The rubric needs an approval volume factor.
2. **Missing property risks are found but rated outside the expected range.** Case 13 (runaway cost on a shared quota) has 87% recall, so the denial of service risk is detected and labeled, but every run tiers it outside the expected range. Case 12 (repudiation) did better than expected at 73% recall. Tiering findings that have no attack path is the gap, and the v0.4.0 design addresses it.
3. **Entry technique versus impact technique.** In the pilot, a run tagged an injection finding with the impact categories (ASI02, ASI03, AML.T0086) and not the entry category (ASI01, AML.T0051). The skill should ask for both.
4. **Design, not runtime.** These evals measure assessments of declared designs. They do not measure whether the assessed agents behave as their designs say.

## What is next

- **v0.3.1:** schema expressiveness fixes found by this batch (element types for stores and peers, planned capabilities, consistent reference checks, clearer guidance on what an attack path step can be), then a new batch.
- **v0.4.0:** STRIDE per element coverage, tiering for missing property findings, an approval volume factor, and entry plus impact tagging, measured against v0.3.1 on the same cases plus new held out cases that were not used for tuning.
