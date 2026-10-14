# PARA eval results

Validator clean means the assessment parsed, matched the schema, and passed every rubric consistency check in skills/para/scripts/validate.py with zero errors. Residual agreement is on the rating rollup (the worst finding); main path residual agreement is on the finding that contains the case's required attack path.

- model: claude-sonnet-5
- provider: anthropic
- endpoint: provider default
- runs_per_case: 5
- temperature: api default
- max_tokens: [64000]
- skill_commit: ab04e7d
- rubric_version: 0.2.2
- schema_version: 0.5.0
- started_at: 2026-10-12T17:53:50+00:00
- last_resumed_at: 2026-10-12T17:53:50+00:00

| Case | Kind | Runs | Validator clean | Recall | Inherent agreement / in range | Residual agreement / in range | Forecast agreement / in range | Main path residual agreement | False positives |
|---|---|---|---|---|---|---|---|---|---|
| 14_heldout_mfa_reset_gate | vulnerable | 5 | 100% | 80% | 100% / 100% | 80% / 100% | 100% / 100% | 80% | 0 |
| 15_heldout_refund_provenance | coverage | 5 | 100% | 100% | 100% / 100% | 80% / 100% | 60% / 100% | n/a | 0 |
| 16_heldout_calendar_injection | vulnerable | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |

Overall: 15 runs, validator clean 100%, mean recall 93%.

Held out cases (written before this version and never used to tune it):
- 14_heldout_mfa_reset_gate: recall 80%, inherent in range 100%, residual in range 100%
- 15_heldout_refund_provenance: recall 100%, inherent in range 100%, residual in range 100%
- 16_heldout_calendar_injection: recall 100%, inherent in range 100%, residual in range 100%
- held out mean recall 93%
Mean output tokens per assessment: 26,325.
