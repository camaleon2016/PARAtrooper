# Validation checklist

Use this when you cannot run `scripts/validate.py` (no code execution, or Python is unavailable). It states every check the validator makes, in plain language. Go through it against your finished JSON, fix every **error**, and explain any **warning** you leave in the rating rationale. Then tell the user validation was manual.

The checks are kept in step with `scripts/validate.py`; when they differ, the script is authoritative.

## Structure

1. **Error:** the document matches `schema/assessment.schema.json`: every required field is present, every enum value is one the schema lists, and no field appears that the schema does not define.
2. **Error:** no id is used twice across inputs, capabilities, controls, elements, and findings.

## References

3. **Error:** every `element.refs` entry is an id defined in the document. An element may link to a protocol `peer_ref` or the subject `agent_id` that shares its own id; any other self reference is circular.
4. **Error:** every `input.reaches_capabilities` entry is a defined capability.
5. **Error:** every `capability.approval_gate_ref` names a defined control.
6. **Error:** every control `covers` entry is an input, capability, element, protocol peer, or the subject agent, never another control.
7. **Error:** every `attack_path` step and every `toxic_combination` entry is an id defined in the document. Artifact locators such as `prompt.md:4-5` belong in `evidence`.

## Controls

8. **Error:** `severs_path` is set only on a control that is structural, independent, and preventive.
9. **Warning:** a behavioral control is not marked independent.
10. **Warning:** every control that is partially dependent or dependent has a `decay_rationale`.
11. **Warning:** every approval gate (any control named by an `approval_gate_ref`) has an `approval_review_mode`. Without one it is scored as `model_summary`.
12. **Warning:** if autonomy is A1 or A2, every capability with sink class S2 or S3 has an `approval_gate_ref`; otherwise score autonomy as A3.

## Findings

13. **Error:** a present finding does not reference a planned element. **Warning:** a forecast finding that references a planned element names a trigger that adds it (`new_tool`, `new_mcp_server`, `new_peer_agent`, or `data_scope_expansion`).
14. **Error:** `residual_risk` is not above `inherent_risk`.
15. **Error:** every finding has a `forecast` block. If no trigger changes the tier, list the triggers you considered and set `projected_risk` equal to `residual_risk`.
16. **Error:** `forecast.projected_risk` is not below `residual_risk`, every `failing_controls` entry is a defined control, and `triggers` is not empty. **Warning:** `watch_signal` is set, and an independent control is listed as failing only under a trigger that can defeat it.
17. **Warning:** for present findings, `inherent_risk` matches the rubric's base matrix and autonomy modifier (rubric section 4).
18. **Warning:** for present findings, `residual_risk` is not below the floor the control credits allow (rubric section 5), and if it is above that floor, `residual_rationale` explains why.
19. **Warning:** any finding with residual above `low` has at least one recommendation.
20. **Error:** a treatment with option `accept` names `treatment.approved_by`.

## Rating and limitations

21. **Error:** `rating.inherent`, `rating.residual`, and `rating.forecast` each equal the highest value of that tier across findings (rubric section 7).
22. **Error:** `limitations` states that the assessment reflects the declared design, not observed runtime behavior.
