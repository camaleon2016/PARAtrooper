# Notes on the Claude results (v0.3.5)

These notes explain [RESULTS.md](RESULTS.md). Every run file is in this folder. The Claude batch it is compared with (v0.3.3) is in [evals/runs](../runs/), and the GPT-5.4 batch on the same commit is in [evals/runs-gpt-54-v035](../runs-gpt-54-v035/).

## How the batch was run

| Setting | Value |
|---|---|
| Model | claude-sonnet-5, Anthropic API |
| Skill commit | efd367e (skill frozen for the whole batch) |
| Rubric / schema | 0.2.2 / 0.5.0, the same as the v0.3.3 batch |
| Cases | the same 13 cases as every batch |
| Runs per case | 5 (65 runs), API default temperature, output limit 64,000 tokens |
| Batch window | 2026-10-12, 00:44 to 07:06 UTC |
| Cost | about $20 at Anthropic list prices, roughly $0.31 per assessment |

Disclosure: the budget guard stopped the first pass after 63 runs, with case 13 at 3 runs. The remaining 2 case 13 runs were completed later on the same commit with the same settings.

## Compared with v0.3.3

| Measure | v0.3.3 | v0.3.5 |
|---|---|---|
| Validator clean | 95% | 100% |
| Mean recall | 96% | 95% |
| Runs with a false positive | 4 (cases 02 and 08) | 2 (case 08) |
| Missing controls recorded per run, mean across cases | 3.9 | 4.5 |
| GitHub MCP backtest: recall, rated critical | 100%, every run | 96%, every run |
| Supabase MCP backtest: recall, rated critical | 88%, every run | 80%, every run |
| Lowest main path residual agreement | 80% | 60% (case 10) |
| Mean output tokens per assessment | 29,264 | 30,309 |

The fixes were aimed at GPT-5.4, and on Claude they did no harm: every run was validator clean for the first time, false positives halved, and slightly more missing controls were recorded. Recall and the backtest recall dipped slightly, within what five runs per case can resolve. Main path agreement fell from 80 to 60 percent in case 10, and from 100 to 80 percent in cases 06 and 11.

## Weaker cases

- **Cases 10 and 11 (backtests):** runs split between the rubric floor for the approval prompt and a stated judgment that the prompt is weaker. That is the approval volume problem both models now show; v0.4.0 addresses it.
- **Case 08 (forecast only):** 2 of 5 runs reported a present finding at `moderate` or above.
- **Case 13** is rated outside the expected range, as on every batch and both models.
