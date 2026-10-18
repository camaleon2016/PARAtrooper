# Notes on the Claude results (v0.4.2)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder. It is compared with the v0.4.0 Claude batch ([runs-claude-v040](../runs-claude-v040/)); `evals/compare.py` reproduces the comparison.

## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5, Anthropic API |
| Skill commit | 0687c45 |
| Rubric / schema | 0.3.2 / 0.6.0 |
| Cases | 16, including 3 held out cases |
| Runs per case | 3 (48 runs), API default temperature, output limit 128,000 tokens, single shot (no repair) |
| Batch date | 2026-10-15 |

## Compared with v0.4.0

| Measure | v0.4.0 | v0.4.2 |
|---|---|---|
| Main path residual agreement | 100% in every case | **100% in every case** |
| Mean recall, cases 01 to 13 | 99% | 96% |
| Held out mean recall | 89% | 93% |
| Runs with a false positive | 1 | 0 |
| Validator clean (single shot) | 98% | 75% |

## Why validity fell, and what it found

This batch first scored 56 percent validator clean. Nineteen failures were property findings (no rate limit, no audit trail) rated at a floor the validator miscalculated: rubric section 5a says behavioral controls never restore a missing property, but the validator credited them anyway. Claude's ratings were right. The validator was fixed in v0.4.2 and the batch rescored, which brought it to 75 percent.

The 12 failures that remain are real under rubric 0.3.2:
- Ten rate a secondary finding above the floor without the `residual_rationale` the rubric now requires. Most are property findings such as no spend cap, no action attribution, or a missing audit trail. Claude ran single shot, so it never saw these errors; GPT-5.4 and Gemini, which had one repair round, corrected nearly all errors of this kind.
- One `severs_path` claim on a control the design lacks, and one id used for both an input and an element.

## Weaker cases

Recall dipped on cases 04 (87 percent), 06 (83), and 05 (92) against 100 percent in v0.4.0; with 3 runs per case, one missed requirement moves a case by 8 to 13 points. Case 13 inherent was in range on 2 of 3 runs.
