# PARA eval results

Validator clean means the assessment parsed, matched the schema, and passed every rubric consistency check in skills/para/scripts/validate.py with zero errors. Residual agreement is on the rating rollup (the worst finding); main path residual agreement is on the finding that contains the case's required attack path.

- model: claude-sonnet-5
- provider: anthropic
- endpoint: provider default
- runs_per_case: 3
- temperature: api default
- max_tokens: [128000]
- skill_commit: 0687c45
- rubric_version: 0.3.2
- schema_version: 0.6.0
- started_at: 2026-10-15T21:26:05+00:00
- last_resumed_at: 2026-10-15T21:26:05+00:00
- repair_rounds: 0

| Case | Kind | Runs | Validator clean | Recall | Inherent agreement / in range | Residual agreement / in range | Forecast agreement / in range | Main path residual agreement | False positives |
|---|---|---|---|---|---|---|---|---|---|
| 01_support_triage | vulnerable | 3 | 100% | 92% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 02_hr_policy_qa | clean | 3 | 100% | 100% | 67% / 100% | 100% / 100% | 67% / 67% | n/a | 0 |
| 03_issue_fixer_self_config | edge | 3 | 100% | 93% | 100% / 100% | 67% / 100% | 100% / 100% | 100% | 0 |
| 04_third_party_mcp_tool_poisoning | vulnerable | 3 | 67% | 87% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 05_a2a_authority_laundering | vulnerable | 3 | 67% | 92% | 100% / 100% | 67% / 100% | 100% / 100% | 100% | 0 |
| 06_summary_gated_payment | edge | 3 | 67% | 83% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 07_memory_poisoning | vulnerable | 3 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 08_forecast_only_new_tool | forecast | 3 | 100% | 100% | 100% / 100% | 100% / 100% | 67% / 100% | n/a | 0 |
| 09_assessor_injection | vulnerable | 3 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 10_backtest_github_mcp | backtest | 3 | 0% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 11_backtest_supabase_mcp | backtest | 3 | 33% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 12_repudiation_shared_identity | coverage | 3 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | n/a | 0 |
| 13_runaway_enrichment_cost | coverage | 3 | 100% | 100% | 67% / 67% | 67% / 67% | 67% / 100% | n/a | 0 |
| 14_heldout_mfa_reset_gate | vulnerable | 3 | 33% | 80% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 15_heldout_refund_provenance | coverage | 3 | 67% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | n/a | 0 |
| 16_heldout_calendar_injection | vulnerable | 3 | 67% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |

Overall: 48 runs, validator clean 75%, mean recall 95%.
STRIDE coverage pairs marked not applicable: 27% on average.

Held out cases (written before this version and never used to tune it):
- 14_heldout_mfa_reset_gate: recall 80%, inherent in range 100%, residual in range 100%
- 15_heldout_refund_provenance: recall 100%, inherent in range 100%, residual in range 100%
- 16_heldout_calendar_injection: recall 100%, inherent in range 100%, residual in range 100%
- held out mean recall 93%
Mean output tokens per assessment: 45,182.

Backtests (would PARA have flagged the incident path and failing control beforehand):
- 10_backtest_github_mcp: recall 100%, inherent in range 100%
- 11_backtest_supabase_mcp: recall 100%, inherent in range 100%
