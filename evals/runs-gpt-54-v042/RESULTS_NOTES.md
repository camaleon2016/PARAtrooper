# Notes on the GPT-5.4 results (v0.4.2)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder; `run_NNN.single.json`, where present, is the first attempt before repair. It is compared with the v0.4.1 repair batch ([runs-gpt-54-v041-repair](../runs-gpt-54-v041-repair/)); `evals/compare.py` reproduces the comparison.

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard, Microsoft Foundry v1 API |
| Skill commit | 0687c45 |
| Rubric / schema | 0.3.2 / 0.6.0 |
| Cases | 16, including 3 held out cases |
| Runs per case | 5 (80 runs), API default settings, output limit 64,000 tokens, 1 repair round |
| Batch date | 2026-10-15 |

Scored with the validator fix released in v0.4.2 (property findings get no credit from behavioral controls, as rubric section 5a says). This batch's repair round ran before that fix, so its repairs answered the old rule; see "Disclosed."

## Compared with v0.4.1

| Measure | v0.4.1 | v0.4.2 |
|---|---|---|
| Validator clean after one repair round | 100% | 99% |
| Validator clean on the first attempt | 79% | 51% |
| Mean recall, cases 01 to 13 | 96% | 95% |
| Held out mean recall | 92% | 93% |
| Runs with a false positive | 0 | 1 |
| Main path agreement, case 07 | 60% | **100%** |
| Main path agreement, held out case 14 | 40% | **80%** |
| Main path agreement below 80% | 07, 14, 16 | 06, 16 |

The two changes aimed at GPT-5.4 worked: counting only prompt instructions that restrict the path as controls brought case 07 to full agreement, and held out case 14 doubled. First attempt validity fell because rubric 0.3.2 now rejects a residual above the floor without a stated reason; one repair round corrects almost all of those.

## Disclosed

- **One run fails the corrected rule.** In case 16, a run's repaired residual is below the floor the corrected validator computes. Its repair round answered the old rule.
- **Main path agreement is 60 percent in cases 06 and 16.** Ratings stayed in range.
- **Case 13 regressed:** recall 67 percent and inherent in range 40 percent, against 87 and 100 percent in v0.4.1. Three of five runs modeled the runaway cost as a path finding rated `critical` rather than a property finding.
- **One false positive** in case 08, the forecast only design.
