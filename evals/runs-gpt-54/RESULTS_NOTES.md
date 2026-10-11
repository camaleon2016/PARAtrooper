# Notes on the GPT-5.4 results (v0.3.4)

These notes explain [RESULTS.md](RESULTS.md), the first PARA batch on a model other than Claude. Every run file is in this folder. `evals/tally_runs.py --runs-dir evals/runs-gpt-54` reproduces the failure breakdown.

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard |
| Endpoint | Microsoft Foundry, Azure OpenAI v1 API (Chat Completions) |
| Skill commit | c59401a (skill frozen for the whole batch) |
| Rubric / schema | 0.2.2 / 0.5.0, the same as the Claude v0.3.3 batch |
| Cases | the same 13 cases as every Claude batch |
| Runs per case | 5 (65 runs); the first run of the 5 smoke cases came from a separate smoke pass |
| Settings | API default temperature and reasoning effort; output limit 64,000 tokens |
| Batch window | 2026-10-11, 04:27 to 04:50 UTC |
| Cost | $4.76 total, $0.073 per assessment, from reported token usage at Azure list prices |

The skill text at c59401a differs from the Claude v0.3.3 batch only in packaging: the v0.3.4 frontmatter, the folder move, and the fallback for platforms that cannot run code. The rubric, schema, and assessment instructions are identical, so the two batches are directly comparable.

## Compared with Claude

| Measure | Claude (v0.3.3 batch) | GPT-5.4 |
|---|---|---|
| Mean recall | 96% | 93% |
| Validator clean | 95% | 92% |
| Runs with a false positive | 4 (cases 02 and 08) | 0 |
| GitHub MCP backtest: recall, rated critical | 100%, every run | 100%, every run |
| Supabase MCP backtest: recall, rated critical | 88%, every run | 100%, every run |
| Lowest main path residual agreement | 80% | 40% (case 07) |
| Mean output tokens per assessment | 29,264 | 4,391 |

The skill ran unchanged on a second model family and produced comparable results: slightly lower recall, no false positives, both incident backtests traced and rated critical, at about one seventh of the output tokens. The case 13 limitation (missing property risks rated outside the expected range) appears on both models, which confirms it comes from the rubric, not the model.

## Depth of the assessments

Shorter output did not mean less work. Averaged per case, GPT-5.4 reported as many or more findings and cited more evidence than Claude in 12 of 13 cases. It recorded about as many declared controls.

It recorded far fewer **missing** controls (`missing_recommended`): for example 0.8 against 5.2 in case 07, 0.2 against 3.6 in case 09, and 1.2 against 5.8 in case 13. It named the fixes in recommendations instead. That leaves reviewers without an explicit list of absent controls, and runs that record different control sets compute different residual floors, which likely contributes to its lower main path agreement in cases 04, 07, and 10.

## Why 5 runs were not validator clean

| Cause | Runs | Cases |
|---|---|---|
| `peer_trust_level` set to `third_party` or `external`, which that field does not allow | 4 | 04, 10 |
| `NIST_AI_RMF` placed in `threat_refs` instead of `governance_refs` | 1 | 12 |

Both are vocabulary confusions the schema invites. `third_party` is a valid value of `subject.trust_domain` but not of `peer_trust_level`, and the governance frameworks live in a different list from the threat frameworks. Claude happened to avoid them; the fix belongs in the schema descriptions and skill guidance, for every model.

## Weaker cases

Recall was lower than Claude's on cases 12 (67 percent against 87), 06 (80 against 93), and 09 (80 against 90). Main path residual agreement fell below the 0.8 target in cases 07 (40 percent), 04 (60), and 10 (60).

## What is next

Two model independent fixes, then a new batch on both models:
- Clearer allowed values for `peer_trust_level` and the framework fields, in the schema and the skill.
- Every structural recommendation must have a matching `missing_recommended` control, with a validator warning when one is missing.

Measuring both fixes on Claude and GPT-5.4 shows whether they improve consistency on two model families, not one.
