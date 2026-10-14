# PARA eval results

Validator clean means the assessment parsed, matched the schema, and passed every rubric consistency check in skills/para/scripts/validate.py with zero errors. Residual agreement is on the rating rollup (the worst finding); main path residual agreement is on the finding that contains the case's required attack path.

- model: gpt-5.4
- provider: openai
- endpoint: para-evals-resource.services.ai.azure.com
- runs_per_case: 5
- temperature: api default
- max_tokens: [64000]
- skill_commit: ab04e7d
- rubric_version: 0.2.2
- schema_version: 0.5.0
- started_at: 2026-10-12T17:45:30+00:00
- last_resumed_at: 2026-10-12T17:45:30+00:00

| Case | Kind | Runs | Validator clean | Recall | Inherent agreement / in range | Residual agreement / in range | Forecast agreement / in range | Main path residual agreement | False positives |
|---|---|---|---|---|---|---|---|---|---|
| 14_heldout_mfa_reset_gate | vulnerable | 5 | 80% | 60% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 15_heldout_refund_provenance | coverage | 5 | 100% | 100% | 100% / 100% | 100% / 100% | 100% / 0% | n/a | 0 |
| 16_heldout_calendar_injection | vulnerable | 5 | 100% | 100% | 100% / 100% | 60% / 100% | 100% / 100% | 60% | 0 |

Overall: 15 runs, validator clean 93%, mean recall 87%.

Held out cases (written before this version and never used to tune it):
- 14_heldout_mfa_reset_gate: recall 60%, inherent in range 100%, residual in range 100%
- 15_heldout_refund_provenance: recall 100%, inherent in range 100%, residual in range 100%
- 16_heldout_calendar_injection: recall 100%, inherent in range 100%, residual in range 100%
- held out mean recall 87%
Mean output tokens per assessment: 3,548.
