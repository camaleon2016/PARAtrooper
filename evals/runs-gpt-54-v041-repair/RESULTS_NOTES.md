# Notes on the GPT-5.4 results with one repair round (v0.4.1)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder: `run_NNN.json` is the final assessment, and `run_NNN.single.json`, where present, is the first attempt before repair.

## What this batch measures

The skill tells the model to run `scripts/validate.py` and fix what it reports, and on agent platforms such as GitHub Copilot it does. The earlier batches were single shot: the model never saw the validator's output. This batch gives GPT-5.4 one repair round. When a first attempt has validator errors, the harness sends back only the validator's own messages and asks for a corrected assessment that changes only what the errors require.

## How the batch was run

| Setting | Value |
|---|---|
| Model | GPT-5.4, Azure deployment, Global Standard, Microsoft Foundry v1 API |
| Skill commit | 9e37b58. The skill, rubric (0.3.1), and schema (0.6.0) are the same as v0.4.0; only the version metadata differs |
| Cases | 16, including the 3 held out cases |
| Runs per case | 5 (80 runs), API default temperature and reasoning effort, output limit 64,000 tokens |
| Repair rounds | 1 |
| Batch date | 2026-10-14 |
| Cost | $9.43 total, $0.118 per assessment, including repair rounds, at Azure list prices |

## Results

| Measure | Value |
|---|---|
| Validator clean on the first attempt | 79% |
| Validator clean after one repair round | **100% (80 of 80)** |
| Mean recall, cases 01 to 13 | 96% |
| Held out mean recall | 92% |
| Runs with a false positive | 0 |
| GitHub and Supabase MCP backtests | 100% recall and 100% main path agreement each |
| Mean output tokens per assessment, including repair | 7,154 |

One repair round fixed every remaining validator error. GPT-5.4's lower single shot validity in v0.4.0 (65 percent) was missing cells and similar slips it corrects when shown them, not a limit of what it can produce. First attempt validity was 79 percent in this batch against 65 percent in the v0.4.0 batch on the same skill, which is variation between batches; both figures are published.

## Disclosed

- **Main path residual agreement fell below 80 percent in three cases:** held out case 14 (40 percent), and cases 07 and 16 (60 percent each). Every rating stayed in the expected range. Repairs can move a residual rating, for example when the validator rejects a residual below the floor, and this batch shows more spread than the single shot v0.4.0 batch.
- **Held out case 14 recall was 76 percent,** against 92 percent single shot in v0.4.0.
- **Case 09** is scored with the corrected evidence check introduced in v0.4.1 (85 percent here).
- **Claude was not rerun with repair.** It was 98 percent validator clean single shot, so there was little to repair, and its runs cost about three times as much.
