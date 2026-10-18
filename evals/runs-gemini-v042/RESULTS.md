# PARA eval results

Validator clean means the assessment parsed, matched the schema, and passed every rubric consistency check in skills/para/scripts/validate.py with zero errors. Residual agreement is on the rating rollup (the worst finding); main path residual agreement is on the finding that contains the case's required attack path.

- model: gemini-3.1-pro-preview
- provider: openai
- endpoint: generativelanguage.googleapis.com
- runs_per_case: 5
- temperature: api default
- max_tokens: [64000]
- skill_commit: 0687c45
- rubric_version: 0.3.2
- schema_version: 0.6.0
- started_at: 2026-10-15T17:13:29+00:00
- last_resumed_at: 2026-10-15T17:27:56+00:00
- repair_rounds: 1

| Case | Kind | Runs | Validator clean | Recall | Inherent agreement / in range | Residual agreement / in range | Forecast agreement / in range | Main path residual agreement | False positives |
|---|---|---|---|---|---|---|---|---|---|
| 01_support_triage | vulnerable | 5 | 100% | 90% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 02_hr_policy_qa | clean | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 80% / 100% | n/a | 0 |
| 03_issue_fixer_self_config | edge | 5 | 80% | 94% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 04_third_party_mcp_tool_poisoning | vulnerable | 5 | 100% | 96% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 05_a2a_authority_laundering | vulnerable | 5 | 100% | 80% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 06_summary_gated_payment | edge | 5 | 100% | 93% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 07_memory_poisoning | vulnerable | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 08_forecast_only_new_tool | forecast | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 80% / 100% | n/a | 0 |
| 09_assessor_injection | vulnerable | 5 | 100% | 80% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 10_backtest_github_mcp | backtest | 5 | 100% | 88% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 11_backtest_supabase_mcp | backtest | 5 | 100% | 88% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 12_repudiation_shared_identity | coverage | 5 | 100% | 80% | 100% / 100% | 100% / 100% | 100% / 100% | n/a | 0 |
| 13_runaway_enrichment_cost | coverage | 5 | 100% | 100% | 60% / 60% | 60% / 60% | 60% / 100% | n/a | 0 |
| 14_heldout_mfa_reset_gate | vulnerable | 5 | 100% | 60% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 15_heldout_refund_provenance | coverage | 5 | 100% | 90% | 100% / 100% | 100% / 100% | 100% / 100% | n/a | 0 |
| 16_heldout_calendar_injection | vulnerable | 5 | 100% | 96% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |

Overall: 80 runs, validator clean 99%, mean recall 90%.
Validator clean on the first attempt, before up to 1 repair round(s): 59%.
STRIDE coverage pairs marked not applicable: 18% on average.

Held out cases (written before this version and never used to tune it):
- 14_heldout_mfa_reset_gate: recall 60%, inherent in range 100%, residual in range 100%
- 15_heldout_refund_provenance: recall 90%, inherent in range 100%, residual in range 100%
- 16_heldout_calendar_injection: recall 96%, inherent in range 100%, residual in range 100%
- held out mean recall 82%
Mean output tokens per assessment: 6,415.

Backtests (would PARA have flagged the incident path and failing control beforehand):
- 10_backtest_github_mcp: recall 88%, inherent in range 100%
- 11_backtest_supabase_mcp: recall 88%, inherent in range 100%
