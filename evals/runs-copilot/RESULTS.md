# PARA eval results

Validator clean means the assessment parsed, matched the schema, and passed every rubric consistency check in skills/para/scripts/validate.py with zero errors. Residual agreement is on the rating rollup (the worst finding); main path residual agreement is on the finding that contains the case's required attack path.

| Case | Kind | Runs | Validator clean | Recall | Inherent agreement / in range | Residual agreement / in range | Forecast agreement / in range | Main path residual agreement | False positives |
|---|---|---|---|---|---|---|---|---|---|
| 01_support_triage | vulnerable | 1 | 100% | 75% | 100% / 100% | 100% / 100% | 100% / 100% | 100% | 0 |
| 10_backtest_github_mcp | backtest | 1 | 100% | 100% | 100% / 100% | 100% / 0% | 100% / 100% | 100% | 0 |

Overall: 2 runs, validator clean 100%, mean recall 88%.

Backtests (would PARA have flagged the incident path and failing control beforehand):
- 10_backtest_github_mcp: recall 100%, inherent in range 100%
