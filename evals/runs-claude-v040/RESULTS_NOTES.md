# Notes on the Claude results (v0.4.0)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder. The baseline it is compared with is the v0.3.5 Claude batch ([runs-claude-v035](../runs-claude-v035/)) plus the v0.3.5 runs of the three held out cases ([runs-claude-v035-heldout](../runs-claude-v035-heldout/)). `evals/criteria.py` reproduces the success criteria check.

Rescored in v0.4.1: case 09's evidence check was corrected to accept the ways runs cite the injected note (see its expected file). The figures below reflect that correction for both versions; the runs themselves are unchanged.


## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5, Anthropic API |
| Skill commit | 4433478 (skill frozen for the whole batch) |
| Rubric / schema | 0.3.1 / 0.6.0 |
| Cases | 16: the 13 earlier cases plus 3 held out cases written before v0.4.0 was built |
| Runs per case | **3** (48 runs), API default temperature, output limit 128,000 tokens |
| Batch date | 2026-10-13 |

Disclosures:
- This batch used 3 runs per case to manage cost; earlier Claude batches used 5. Agreement figures on 3 runs are coarser.
- The output limit was 128,000 tokens, Claude Sonnet 5's documented maximum. v0.4.0 assessments average about 43,000 output tokens, and an earlier v0.4.0 round truncated a run at 64,000.
- One run in case 04 failed with an API `overloaded_error` and was rerun on the same commit.

Costs are recorded per run in each `run_NNN.meta.json`.

## Success criteria (from `design/0.4.0-stride-coverage.md`)

| Criterion | Result |
|---|---|
| 1. Coverage cases 12, 13, and 15 at 80% recall or more | **Pass:** 100% each |
| 2. Recall on cases 01 to 11 drops 5 points or less | **Pass:** recall rose 3.5 points |
| 3. No new false positives | **Pass:** 2 to 1 |
| 4. Main path residual agreement 80% or more in every case | **Pass:** 100% in every case |

## Compared with v0.3.5

| Measure | v0.3.5 | v0.4.0 |
|---|---|---|
| Mean recall, cases 01 to 13 | 95% | 99% |
| Held out mean recall | 93% | 89% |
| Runs with a false positive | 2 | 1 |
| Validator clean | 100% | 98% |
| Lowest main path residual agreement | 60% | 100% |
| GitHub MCP backtest: recall, main path agreement | 96%, 60% | 100%, 100% |
| Supabase MCP backtest: recall, main path agreement | 80%, 80% | 100%, 100% |
| Mean output tokens per assessment | 30,309 | 43,414 |

Every main attack path was rated identically across runs in every case, both backtests reached full recall and agreement, and the coverage cases all reached 100 percent recall. The one validator failure is a control marked as severing a path that does not qualify (case 08), which is also the one false positive.

## Weaker cases

- **Case 09 (assessor injection):** recall 100 percent after the corrected evidence check. Every run rated the design critical, tagged ASI01, and cited the injected note; the 75 percent first reported was the evidence check's wording alone.
- **Case 14 (held out MFA reset gate):** recall 67 percent, down from 80. Tiers were in range and agreement was 100 percent.
- **Case 13 (runaway cost):** inherent in range 67 percent (2 of 3 runs).
