# Notes on the GPT-5.4 results (v0.4.0)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder. The baseline it is compared with is the v0.3.5 GPT-5.4 batch ([runs-gpt-54-v035](../runs-gpt-54-v035/)) plus the v0.3.5 runs of the three held out cases ([runs-gpt-54-v035-heldout](../runs-gpt-54-v035-heldout/)). `evals/criteria.py` reproduces the success criteria check.

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard, Microsoft Foundry v1 API |
| Skill commit | 4433478 (skill frozen for the whole batch) |
| Rubric / schema | 0.3.1 / 0.6.0 |
| Cases | 16: the 13 earlier cases plus 3 held out cases written before v0.4.0 was built |
| Runs per case | 5 (80 runs), API default temperature and reasoning effort, output limit 64,000 tokens |
| Batch date | 2026-10-13 |

Costs are recorded per run in each `run_NNN.meta.json`.

## Success criteria (from `design/0.4.0-stride-coverage.md`)

| Criterion | Result |
|---|---|
| 1. Coverage cases 12, 13, and 15 at 80% recall or more | **Pass:** 100%, 93%, 100% |
| 2. Recall on cases 01 to 11 drops 5 points or less | **Pass:** recall rose 1.1 points |
| 3. No new false positives | **Pass:** 1 to 0 |
| 4. Main path residual agreement 80% or more in every case | **Miss:** case 05 at 60% |

## Compared with v0.3.5

| Measure | v0.3.5 | v0.4.0 |
|---|---|---|
| Mean recall, cases 01 to 13 | 93% | 96% |
| Held out mean recall | 87% | 97% |
| Runs with a false positive | 1 | 0 |
| Validator clean | 98% | **65%** |
| GitHub MCP backtest: recall, main path agreement | 100%, 60% | 100%, 100% |
| Supabase MCP backtest: recall, main path agreement | 92%, 80% | 100%, 100% |
| STRIDE pairs marked not applicable | n/a | 30% |
| Mean output tokens per assessment | 4,413 | 5,836 |

The substance improved. Recall rose, the held out cases rose from 87 to 97 percent (case 14 from 60 to 92), false positives fell to zero, and the approval volume factor brought both backtests to full main path agreement.

## Why validity fell, stated plainly

Validator clean fell from 98 to 65 percent. v0.4.0 asks every assessment for a complete STRIDE per element matrix, and GPT-5.4, which writes short assessments, often leaves cells out:

| Cause | Runs |
|---|---|
| A required STRIDE pair with no entry (most often spoofing for an external server or person, or denial of service for a memory store) | 16 |
| Residual rated below the floor the controls allow, now an error in rubric 0.3.x | 6 |
| A recommendation category of `behavioral`, which belongs in `mechanism` | 3 |
| Coverage that names a category an external entity cannot carry | 2 |
| `mitigated` with no control named | 2 |
| A missing control cited as a mitigation | 1 |

These evals are single shot: the model gets no chance to act on validator errors. On agent platforms such as GitHub Copilot, the skill runs its own validator and corrects what it reports, so real world validity should be higher. That has not been measured yet; v0.4.1 adds a repair pass to the harness to measure it.

## Weaker cases

- **Case 05 (A2A authority laundering):** main path agreement 60 percent; two runs rated residual below the floor and were rejected.
- **Case 13 (runaway cost):** inherent in range 60 percent. The property finding rule moved it from 0 percent in every earlier batch, but not every run applies it.
- **Case 09 (assessor injection):** recall 75 percent, unchanged from v0.3.5.
