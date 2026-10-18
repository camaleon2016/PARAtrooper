# Notes on the Gemini results (v0.4.2)

These notes explain [RESULTS.md](RESULTS.md), the first PARA batch on a third model family. Every run file is in this folder; `run_NNN.single.json`, where present, is the first attempt before repair.

## How the batch was run

| Setting | Value |
|---|---|
| Model | **gemini-3.1-pro-preview**, Gemini API through its OpenAI compatible endpoint |
| Skill commit | 0687c45, unchanged for this model |
| Rubric / schema | 0.3.2 / 0.6.0 |
| Cases | 16, including 3 held out cases |
| Runs per case | 5 (80 runs), API default settings, output limit 64,000 tokens, 1 repair round |
| Batch date | 2026-10-15 |

**Preview model disclosure.** Google can change a preview model without notice, so these results may not reproduce later. A rerun on a generally available Gemini Pro model, once one is released at this level, would be the cleaner record.

Scored with the validator fix released in v0.4.2; this batch's repair round ran before it.

## Results

| Measure | Value |
|---|---|
| Main path residual agreement | **100% in every case** |
| Validator clean after one repair round | 99% |
| Validator clean on the first attempt | 59% |
| Mean recall, cases 01 to 13 | 91% |
| Held out mean recall | 82% |
| Runs with a false positive | 0 |
| GitHub and Supabase MCP backtests | 88% recall each, rated critical in every run |
| Mean output tokens per assessment | 6,415 |

The unchanged skill ran on a third model family with full main path agreement and no false positives. Recall is lower than on Claude and GPT-5.4, mostly from a few required items missed consistently.

## Weaker cases

- **Held out case 14:** recall 60 percent, with every tier in range.
- **Cases 05, 09, and 12:** recall 80 percent each.
- **Case 13:** inherent in range on 3 of 5 runs.
- **One run in case 03** fails the corrected floor rule; its repair answered the old rule.
