"""Validate a PARA assessment against the schema, referential integrity, and rubric invariants.

Usage: python scripts/validate.py <assessment.json> [--schema PATH] [--strict]
Exit code 0 = valid, 1 = errors (or warnings with --strict), 2 = usage or I/O problem.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

TIERS = ["low", "moderate", "high", "critical"]
RANK = {t: i for i, t in enumerate(TIERS)}
DEFAULT_SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "assessment.schema.json"
SENSITIVITY_RANK = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
AUTONOMY_MODIFIER_STEP_LIMIT = 25

# Rubric section 4 base matrix: source class x sink class.
BASE_MATRIX = {
    "U": {3: "critical", 2: "high", 1: "moderate", 0: "low"},
    "I": {3: "high", 2: "moderate", 1: "low", 0: "low"},
    "T": {3: "moderate", 2: "low", 1: "low", 0: "low"},
}


def tier_max(tiers):
    return max(tiers, key=RANK.__getitem__) if tiers else "low"


def shift(tier: str, steps: int) -> str:
    return TIERS[max(0, min(len(TIERS) - 1, RANK[tier] + steps))]


def source_class(inp: dict) -> str:
    return {"trusted": "T", "internal": "I"}.get(inp.get("trust_level"), "U")


def sink_class(cap: dict, carried_sensitivity: int) -> int:
    action = cap.get("action")
    sens = max(SENSITIVITY_RANK[cap["data_sensitivity"]], carried_sensitivity)
    scope = cap.get("credential_scope", "unknown")
    egress = cap.get("is_egress", False)
    if (
        cap.get("reversibility") == "irreversible"
        or (egress and sens >= 2)
        or action in {"spend", "credential_access", "configure", "delegate"}
        or (action == "execute" and scope != "least_privilege")
    ):
        return 3
    if (action in {"write", "delete"} and sens >= 1) or (egress and sens >= 1) or action == "execute":
        return 2
    if (action == "read" and sens >= 1) or action == "write":
        return 1
    return 0


def expected_inherent(finding: dict, inputs: dict, caps: dict, autonomy: dict) -> str | None:
    """Recompute inherent tier from the attack path per rubric sections 2 to 4. None if not computable."""
    refs = [s["ref"] for s in finding.get("attack_path", [])]
    srcs = [inputs[r] for r in refs if r in inputs]
    path_caps = [caps[r] for r in refs if r in caps]
    if not srcs or not path_caps:
        return None
    src = min((source_class(s) for s in srcs), key="UIT".index)
    carried, sink = 0, 0
    for cap in path_caps:
        sink = max(sink, sink_class(cap, carried))
        if cap.get("action") == "read":
            carried = max(carried, SENSITIVITY_RANK[cap["data_sensitivity"]])
    tier = BASE_MATRIX[src][sink]
    level = autonomy.get("level")
    if level == "A0_suggest_only":
        return "low"
    steps = autonomy.get("max_unattended_steps")
    unbounded = (steps is None or steps > AUTONOMY_MODIFIER_STEP_LIMIT) and autonomy.get("max_runtime_minutes") is None
    if sink >= 2 and (
        level == "A4_fully_autonomous"
        or autonomy.get("can_spawn_agents")
        or autonomy.get("can_modify_own_config")
        or unbounded
    ):
        tier = shift(tier, 1)
    return tier


def residual_floor(finding: dict, caps: dict, controls: dict) -> str:
    """Lowest residual that rubric section 5 credits can justify for the controls on the path.

    Each control earns credit at exactly one step:
      step 1: structural, independent, preventive, severs_path true -> residual low
      step 2: human approval gate on a path capability -> -2, floor moderate unless raw_action review
      step 3: other structural preventive or containment controls that are not dependent -> -1 total
      step 4: behavioral or dependent preventive or containment controls -> -1 total
      step 5: detective and corrective controls -> no tier credit
    """
    refs = {s["ref"] for s in finding.get("attack_path", [])}
    gate_ids = {caps[r].get("approval_gate_ref") for r in refs if r in caps} - {None}
    on_path = [
        c for c in controls.values()
        if c["status"] != "missing_recommended" and (refs & set(c.get("covers", [])) or c["control_id"] in gate_ids)
    ]
    gates = [c for c in on_path if c["control_id"] in gate_ids]
    others = [c for c in on_path if c["control_id"] not in gate_ids and c["category"] in {"preventive", "containment"}]

    if any(
        c.get("severs_path") and c["mechanism"] == "structural"
        and c["capability_dependence"] == "independent" and c["category"] == "preventive"
        for c in others
    ):
        return "low"

    credit, floor = 0, "low"
    if gates:
        credit += 2
        if not any(g.get("approval_review_mode") == "raw_action" for g in gates):
            floor = "moderate"
    if any(c["mechanism"] == "structural" and c["capability_dependence"] != "dependent" for c in others):
        credit += 1
    if any(c["mechanism"] == "behavioral" or c["capability_dependence"] == "dependent" for c in others):
        credit += 1

    inherent = finding["inherent_risk"]
    floor = floor if RANK[floor] <= RANK[inherent] else inherent
    return tier_max([shift(inherent, -credit), floor])


def check(doc: dict, schema: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"schema: {path}: {err.message}")
    if errors:
        return errors, warnings  # Semantic checks assume a structurally valid document.

    caps = {c["capability_id"]: c for c in doc["capabilities"]}
    inputs = {i["input_id"]: i for i in doc["inputs"]}
    controls = {c["control_id"]: c for c in doc["controls"]}
    findings = doc["findings"]

    all_ids: dict[str, str] = {}
    for kind, items, key in (
        ("capability", doc["capabilities"], "capability_id"),
        ("input", doc["inputs"], "input_id"),
        ("control", doc["controls"], "control_id"),
        ("finding", findings, "finding_id"),
    ):
        for item in items:
            ident = item[key]
            if ident in all_ids:
                errors.append(f"duplicate id '{ident}' ({all_ids[ident]} and {kind})")
            all_ids[ident] = kind

    known_refs = set(caps) | set(inputs) | set(controls) | {doc["subject"]["agent_id"]}
    known_refs |= {p["peer_ref"] for p in doc.get("protocols", [])}

    for inp in doc["inputs"]:
        for ref in inp.get("reaches_capabilities", []):
            if ref not in caps:
                errors.append(f"inputs/{inp['input_id']}: reaches unknown capability '{ref}'")
    for cap in doc["capabilities"]:
        gate = cap.get("approval_gate_ref")
        if gate and gate not in controls:
            errors.append(f"capabilities/{cap['capability_id']}: approval_gate_ref '{gate}' is not a control")
    for ctl in doc["controls"]:
        for ref in ctl.get("covers", []):
            if ref not in caps and ref not in inputs:
                errors.append(f"controls/{ctl['control_id']}: covers unknown id '{ref}'")
        if ctl["mechanism"] == "behavioral" and ctl["capability_dependence"] == "independent":
            warnings.append(
                f"controls/{ctl['control_id']}: behavioral control marked independent; see control_decay.md rule 3"
            )
        if ctl.get("severs_path") and not (
            ctl["mechanism"] == "structural" and ctl["capability_dependence"] == "independent"
            and ctl["category"] == "preventive"
        ):
            errors.append(
                f"controls/{ctl['control_id']}: severs_path requires a structural, independent, preventive control "
                "(rubric section 5 step 1)"
            )
        if ctl["capability_dependence"] != "independent" and not ctl.get("decay_rationale"):
            warnings.append(f"controls/{ctl['control_id']}: {ctl['capability_dependence']} control has no decay_rationale")

    gate_refs = {c.get("approval_gate_ref") for c in doc["capabilities"]} - {None}
    for gid in sorted(gate_refs & set(controls)):
        if not controls[gid].get("approval_review_mode"):
            warnings.append(
                f"controls/{gid}: approval gate has no approval_review_mode; scored as model_summary (floor moderate)"
            )

    level = doc["autonomy"]["level"]
    if level in {"A1_act_with_approval_each_step", "A2_act_with_approval_on_sensitive"}:
        for cap in doc["capabilities"]:
            if sink_class(cap, 0) >= 2 and not cap.get("approval_gate_ref"):
                warnings.append(
                    f"autonomy: {level} declared but {cap['capability_id']} has no approval_gate_ref; score it as A3"
                )

    for f in findings:
        fid = f"findings/{f['finding_id']}"
        for step in f.get("attack_path", []):
            if step["ref"] not in known_refs:
                errors.append(f"{fid}: attack_path ref '{step['ref']}' not defined in document")
        for ref in f.get("toxic_combination", []):
            if ref not in known_refs:
                errors.append(f"{fid}: toxic_combination ref '{ref}' not defined in document")
        if RANK[f["residual_risk"]] > RANK[f["inherent_risk"]]:
            errors.append(f"{fid}: residual_risk {f['residual_risk']} exceeds inherent_risk {f['inherent_risk']}")
        fc = f.get("forecast")
        if f["horizon"] == "forecast" and not fc:
            errors.append(f"{fid}: horizon is forecast but no forecast block")
        if fc:
            if RANK[fc["projected_risk"]] < RANK[f["residual_risk"]]:
                errors.append(f"{fid}: projected_risk {fc['projected_risk']} below residual_risk {f['residual_risk']}")
            for cid in fc["failing_controls"]:
                if cid not in controls:
                    errors.append(f"{fid}: failing_control '{cid}' not in controls")
                elif (controls[cid]["capability_dependence"] == "independent"
                      and not {"control_removal", "autonomy_increase", "data_scope_expansion"} & set(fc["triggers"])):
                    warnings.append(f"{fid}: independent control '{cid}' listed as failing without a trigger that defeats it")
            if not fc["triggers"]:
                errors.append(f"{fid}: forecast has no triggers")
            if not fc.get("watch_signal"):
                warnings.append(f"{fid}: forecast has no watch_signal")

        if f["horizon"] == "present":
            exp = expected_inherent(f, inputs, caps, doc["autonomy"])
            if exp and exp != f["inherent_risk"]:
                warnings.append(f"{fid}: rubric computes inherent '{exp}', document says '{f['inherent_risk']}'")
            floor = residual_floor(f, caps, controls)
            if RANK[f["residual_risk"]] < RANK[floor]:
                warnings.append(f"{fid}: residual '{f['residual_risk']}' is below what path controls can justify ('{floor}')")
        if not f.get("recommendations") and RANK[f["residual_risk"]] >= RANK["moderate"]:
            warnings.append(f"{fid}: residual {f['residual_risk']} with no recommendations")
        if f.get("treatment", {}).get("option") == "accept" and not f["treatment"].get("approved_by"):
            errors.append(f"{fid}: accepted risk requires treatment.approved_by (ISO/IEC 42001 6.1.3)")

    present = [f for f in findings if f["horizon"] == "present"]
    want = {
        "inherent": tier_max([f["inherent_risk"] for f in present]),
        "residual": tier_max([f["residual_risk"] for f in present]),
    }
    want["forecast"] = tier_max([want["residual"]] + [f["forecast"]["projected_risk"] for f in findings if f.get("forecast")])
    for key, val in want.items():
        if doc["rating"][key] != val:
            errors.append(f"rating.{key} is '{doc['rating'][key]}' but rollup of findings gives '{val}' (rubric section 7)")

    if not any("runtime" in lim.lower() for lim in doc["limitations"]):
        errors.append("limitations: must state that the assessment reflects design, not observed runtime behavior")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("assessment", type=Path)
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    try:
        doc = json.loads(args.assessment.read_text(encoding="utf-8"))
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    errors, warnings = check(doc, schema)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARN    {w}")
    ok = not errors and not (args.strict and warnings)
    print(f"{'VALID' if ok else 'INVALID'}: {args.assessment} ({len(errors)} errors, {len(warnings)} warnings)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
