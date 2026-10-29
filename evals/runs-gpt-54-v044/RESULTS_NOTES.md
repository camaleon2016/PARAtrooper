# Notes on the GPT-5.4 results (v0.4.4)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder; `run_NNN.single.json`, where present, is the first attempt before repair. It is compared with the v0.4.2 GPT-5.4 batch ([runs-gpt-54-v042](../runs-gpt-54-v042/)).

## What v0.4.4 tested

One question: does a final self check in the skill ("every finding above its floor must state why in `residual_rationale`") raise first attempt validity? The rubric and schema did not change, so ratings should not move.

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard, Microsoft Foundry v1 API |
| Skill commit | 4509c84 |
| Rubric / schema | 0.3.2 / 0.6.1 |
| Cases | 16, including 3 held out cases |
| Runs per case | 5 (80 runs), API default settings, output limit 64,000 tokens, 1 repair round |
| Batch date | 2026-10-28 |

## Result: the self check did not help

| Measure | v0.4.2 | v0.4.4 |
|---|---|---|
| Validator clean on the first attempt | 51% | **48%** |
| Validator clean after one repair round | 99% | 95% |
| Mean recall, cases 01 to 13 | 95% | 95% |
| Held out mean recall | 93% | 96% |
| Runs with a false positive | 1 | 0 |
| Main path agreement below 80% | 06, 16 | 05, 14 |

First attempt validity did not improve; the difference is within run to run variation. Ratings held, as expected. Two runs still rated a secondary finding above the floor without a rationale after repair, the same error the self check targeted.

Interpretation: the omission is not carelessness that a reminder fixes. The runs consistently judge the floor too low for certain secondary findings, most often an unpinned or unverified MCP server, where the floor credits an approval prompt that shows a model written summary. A summary written in a context the compromised server can influence is a weak defense against that server. The next step is to test a rubric refinement for that situation, measured on its own.

## Other failures

- One `mitigated` STRIDE entry with no control named (case 12).
- One rollup that did not match its findings (case 16).
