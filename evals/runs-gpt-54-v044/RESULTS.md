# PARA eval results

Validator clean means the assessment parsed, matched the schema, and passed every rubric consistency check in skills/para/scripts/validate.py with zero errors. Residual agreement is on the rating rollup (the worst finding); main path residual agreement is on the finding that contains the case's required attack path.

- model: gpt-5.4
- provider: openai
- endpoint: para-evals-resource.services.ai.azure.com
- runs_per_case: 5
- temperature: api default
- max_tokens: [64000]
- skill_commit: 4509c84
- rubric_version: 0.3.2
- schema_version: 0.6.1
- started_at: 2026-10-28T20:38:23+00:00
- last_resumed_at: 2026-10-28T20:38:23+00:00
- repair_rounds: 1

| Case | Kind | Runs | Validator clean | Recall | Inherent agreement / in range | Residual agreement / in range | Forecast agreement / in range | Main path residual agreement | False positives |
|---|---|---|---|---|---|---|---|---|---|
| 01_support_triage | vulnerable | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 02_hr_policy_qa | clean | 5 | 100% | 100% | 80% / 100% | 100% / 100% | 80% / 100% | n/a | 0 |
| 03_issue_fixer_self_config | edge | 5 | 100% | 98% | 100% / 100% | 80% / 100% | 100% / 100% | 100% | 0 |
| 04_third_party_mcp_tool_poisoning | vulnerable | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 05_a2a_authority_laundering | vulnerable | 5 | 100% | 95% | 100% / 100% | 60% / 100% | 100% / 100% | 60% | 0 |
| 06_summary_gated_payment | edge | 5 | 100% | 97% | 100% / 100% | 100% / 100% | 100% / 100% | 80% | 0 |
| 07_memory_poisoning | vulnerable | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 08_forecast_only_new_tool | forecast | 5 | 100% | 87% | 80% / 100% | 100% / 100% | 80% / 80% | n/a | 0 |
| 09_assessor_injection | vulnerable | 5 | 100% | 85% | 100% / 100% | 80% / 100% | 100% / 100% | 80% | 0 |
| 10_backtest_github_mcp | backtest | 5 | 80% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 11_backtest_supabase_mcp | backtest | 5 | 80% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 12_repudiation_shared_identity | coverage | 5 | 80% | 87% | 100% / 100% | 100% / 100% | 100% / 100% | n/a | 0 |
| 13_runaway_enrichment_cost | coverage | 5 | 100% | 80% | 80% / 80% | 80% / 80% | 80% / 100% | n/a | 0 |
| 14_heldout_mfa_reset_gate | vulnerable | 5 | 100% | 88% | 100% / 100% | 60% / 100% | 100% / 100% | 60% | 0 |
| 15_heldout_refund_provenance | coverage | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | n/a | 0 |
| 16_heldout_calendar_injection | vulnerable | 5 | 80% | 100% | 100% / 100% | 60% / 100% | 100% / 100% | 80% | 0 |

Overall: 80 runs, validator clean 95%, mean recall 95%.
Validator clean on the first attempt, before up to 1 repair round(s): 48%.
STRIDE coverage pairs marked not applicable: 28% on average.

Held out cases (written before this version and never used to tune it):
- 14_heldout_mfa_reset_gate: recall 88%, inherent in range 100%, residual in range 100%
- 15_heldout_refund_provenance: recall 100%, inherent in range 100%, residual in range 100%
- 16_heldout_calendar_injection: recall 100%, inherent in range 100%, residual in range 100%
- held out mean recall 96%
Mean output tokens per assessment: 9,119.

Backtests (would PARA have flagged the incident path and failing control beforehand):
- 10_backtest_github_mcp: recall 100%, inherent in range 100%
- 11_backtest_supabase_mcp: recall 100%, inherent in range 100%
