# Notes on the GPT-5.4 results (v0.4.5)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder; `run_NNN.single.json`, where present, is the first attempt before repair. It is compared with the v0.4.4 batch ([runs-gpt-54-v044](../runs-gpt-54-v044/)). An earlier v0.4.5 round, run before the fix described below, is in [archive/0.4.5-pre](../archive/0.4.5-pre/NOTES.md).

## What v0.4.5 changed

Rubric 0.3.3 aligns two credit rules with what runs on every model kept concluding:
- **Property findings:** only a control that restores the missing property earns credit. Approval prompts, prompt instructions, allowlists, and ordinary logs earn nothing.
- **Supply chain findings (ASI04):** approval prompts and prompt instructions earn no credit against a compromised or unverified component.

A property finding whose inherent tier does not follow section 5a is now an error.

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard, Microsoft Foundry v1 API |
| Skill commit | 0e00ec3 |
| Rubric / schema | 0.3.3 / 0.6.2 |
| Cases | 16, including 3 held out cases |
| Runs per case | 5 (80 runs), API default settings, output limit 64,000 tokens, 1 repair round |
| Batch date | 2026-10-29 |

## Compared with v0.4.4

| Measure | v0.4.4 | v0.4.5 |
|---|---|---|
| Validator clean on the first attempt | 48% | **56%** |
| Validator clean after one repair round | 95% | 91% |
| Mean recall, cases 01 to 13 | 95% | 95% |
| Held out mean recall | 96% | 96% |
| Runs with a false positive | 0 | 0 |
| Residual in range | every case except 13 (80%) | **every case** |
| Main path agreement below 80% | 05, 14 | 05, 06, 07, 14 (60% each) |

The changes did what they were aimed at. First attempt validity rose 8 points, because runs stopped rating findings above floors that had credited irrelevant controls, and every residual landed in its expected range. The stricter property check gives the first attempt one more way to fail, which is why the gain is smaller than the 69 percent a rescoring of v0.4.4 runs predicted.

Two figures moved the wrong way and are disclosed here. Validator clean after repair fell from 95 to 91 percent: seven runs kept an error through the repair round, mostly a rollup that did not match its findings or a residual left below its floor. Main path agreement fell below 80 percent in two more cases. With five runs per case, each of those is one run, so neither is clearly a regression; both are worth watching in the next batch.

## Remaining failures

| Error | Runs |
|---|---|
| Residual below the floor (a property finding rated `low` after declaring a higher inherent tier) | 2 |
| `rating.residual` does not match the worst finding | 2 |
| `mitigated` STRIDE entry with no control named | 1 |
| A control that covers another control | 1 |
| Residual above inherent | 1 |

Case 13's recall was 73 percent (80 in v0.4.4); its tiers were in range in every run.
