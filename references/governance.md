# Governance Mapping

PARA performs parts of NIST AI RMF MAP and MEASURE. It produces inputs for MANAGE, and it records GOVERN facts. For ISO/IEC 42001, it is a candidate 6.1.2 methodology and it produces 8.2 records.

Clause, Annex A, and subcategory ids here were checked against ISO/IEC 42001:2023 and NIST AI RMF 1.0. Recheck them when either edition changes.

## NIST AI RMF 1.0

| Function | PARA workflow step | Schema fields | Subcategories |
|---|---|---|---|
| MAP | 2 to 4: inventory capabilities, inputs, and autonomy | `capabilities`, `inputs`, `autonomy`, `subject` | MAP 1.1 (context), MAP 4.1 (third party components), MAP 5.1 (likelihood and magnitude of impacts) |
| MEASURE | 7 to 9: classify controls, find paths, compute tiers | `controls`, `findings`, `rating` | MEASURE 2.7 (security and resilience), MEASURE 3.1 (emergent risks tracked; this is where the forecast fits), MEASURE 1.1 (methods and metrics) |
| MANAGE | Recommendations and treatment | `findings[].recommendations`, `findings[].treatment` | MANAGE 1.3 (responses to high priority risks), MANAGE 3.1 (third party risk), MANAGE 4.1 (post deployment monitoring) |
| GOVERN | Owners, approvals, reassessment | `controls[].owner`, `treatment.approved_by`, `assessment.assessment_reason` | GOVERN 1.5 (periodic review), GOVERN 6.1 (third party policies) |

The forecast maps most closely to **MEASURE 3.1**. That subcategory asks organizations to identify and track emergent risk, and the forecast turns it into a list of named controls to watch.

## ISO/IEC 42001:2023

| Clause | Requirement (paraphrased) | PARA evidence |
|---|---|---|
| 6.1.2 | A documented risk assessment process that gives consistent, valid, and comparable results, and considers likelihood and consequence | `rubric.md` (method); `evals/run_consistency.py` output (consistency evidence); `likelihood` and `consequence` fields |
| 6.1.3 | Risk treatment options, comparison with Annex A, management approval | `treatment` block; `recommendations[].governance_refs` pointing to Annex A controls |
| 6.1.4 | AI system impact assessment | **Out of scope.** PARA hands off to the organization's impact assessment and does not do it. |
| 8.2 | Assessment at planned intervals and on significant change | `assessment_reason`, `change_triggers`, `previous_assessment_id`. Forecast triggers are the documented significant change criteria. |
| 8.3 | Implement the risk treatment plan | `treatment.option`, `owner`, `review_by` |

**The link to the preemptive thesis:** 8.2 requires reassessment when significant changes occur. PARA's forecast states in advance which changes are significant for *this* agent and which controls those changes would defeat. An auditor can check afterward whether a reassessment was triggered.

## Evidence package for an auditor

1. The assessment JSON (validated) and the rendered reviewer report
2. The rubric version used (`assessment.assessor.rubric_version`)
3. Consistency results for the rubric version (`evals/run_consistency.py`)
4. The chain of `previous_assessment_id` values, which shows reassessment history
