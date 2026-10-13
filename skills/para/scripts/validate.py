"""Validate a PARA assessment against the schema, referential integrity, and rubric invariants.

Usage: python scripts/validate.py <assessment.json> [--schema PATH] [--strict]
Exit code 0 = valid, 1 = errors (or warnings with --strict), 2 = usage or I/O problem.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # Optional: many agent sandboxes lack it. Rubric checks still run without it.
    Draft202012Validator = None
    FormatChecker = None

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


CONSEQUENTIAL_ACTIONS = {"write", "delete", "execute", "configure", "spend", "delegate", "credential_access"}


def is_consequential(cap: dict) -> bool:
    """Rubric section 5a, consequence: the capability changes something or moves data out."""
    return cap.get("action") in CONSEQUENTIAL_ACTIONS or bool(cap.get("is_egress"))


def finding_refs(finding: dict) -> list[str]:
    """The ids a finding is about: its attack path, or for a property finding its affected_refs."""
    if finding.get("finding_kind") == "property":
        return list(finding.get("affected_refs", []))
    return [s["ref"] for s in finding.get("attack_path", [])]


def autonomy_shift(tier: str, sink: int, autonomy: dict) -> str:
    """Rubric section 4 autonomy modifier."""
    steps = autonomy.get("max_unattended_steps")
    unbounded = (steps is None or steps > AUTONOMY_MODIFIER_STEP_LIMIT) and autonomy.get("max_runtime_minutes") is None
    if sink >= 2 and (
        autonomy.get("level") == "A4_fully_autonomous"
        or autonomy.get("can_spawn_agents")
        or autonomy.get("can_modify_own_config")
        or unbounded
    ):
        return shift(tier, 1)
    return tier


def expected_inherent(finding: dict, inputs: dict, caps: dict, autonomy: dict) -> str | None:
    """Recompute inherent tier per rubric sections 2 to 4, or section 5a for property findings.
    None if not computable."""
    if autonomy.get("level") == "A0_suggest_only":
        return "low"
    if finding.get("finding_kind") == "property":
        # Section 5a: a missing property is exposed to internal error and misuse as readily as to an
        # attacker, so it uses the I row; alone it never reaches critical.
        affected = [caps[r] for r in finding.get("affected_refs", []) if r in caps]
        if not affected:
            return None
        if not any(is_consequential(c) for c in affected):
            return "low"  # rubric 0.3.1: a missing property on read and answer capabilities is hygiene
        sink = max(sink_class(c, 0) for c in affected)
        tier = autonomy_shift(BASE_MATRIX["I"][sink], sink, autonomy)
        return tier if RANK[tier] <= RANK["high"] else "high"
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
    return autonomy_shift(BASE_MATRIX[src][sink], sink, autonomy)


def residual_floor(finding: dict, caps: dict, controls: dict) -> str:
    """Lowest residual that rubric section 5 credits can justify for the controls on the path.

    Each control earns credit at exactly one step:
      step 1: structural, independent, preventive, severs_path true -> residual low
      step 2: human approval gate on a path capability. Low approval volume: -2. High or unknown
              volume: -1. Floor moderate unless the gate shows the raw action and volume is low.
      step 3: other structural preventive or containment controls that are not dependent and that
              constrain the path's sink (constrains_sink true) -> -1 total
      step 4: behavioral or dependent preventive or containment controls -> -1 total
      step 5: detective and corrective controls -> no tier credit
    """
    refs = set(finding_refs(finding))
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
        low_volume = any(g.get("approval_volume") == "low" for g in gates)
        credit += 2 if low_volume else 1
        if not any(g.get("approval_review_mode") == "raw_action" and g.get("approval_volume") == "low" for g in gates):
            floor = "moderate"
    if any(c["mechanism"] == "structural" and c["capability_dependence"] != "dependent" and c.get("constrains_sink")
           for c in others):
        credit += 1
    if any(c["mechanism"] == "behavioral" or c["capability_dependence"] == "dependent" for c in others):
        credit += 1

    inherent = finding["inherent_risk"]
    floor = floor if RANK[floor] <= RANK[inherent] else inherent
    return tier_max([shift(inherent, -credit), floor])


# STRIDE per element (stride_agentic.md). Data flows need coverage only when they cross a boundary;
# a data store needs repudiation only when it is an audit record.
def schema_at_least(version: str, minimum: tuple[int, int, int]) -> bool:
    """Rules introduced in a schema version apply only to documents that declare it, so earlier
    assessments (for example, baseline runs of an older skill) are judged by the rules they targeted."""
    try:
        return tuple(int(x) for x in version.split(".")[:3]) >= minimum
    except ValueError:
        return True


# Categories an element kind can carry at all. Covering more than the required set is allowed.
POSSIBLE = {
    "process": ["spoofing", "tampering", "repudiation", "information_disclosure", "denial_of_service",
                "elevation_of_privilege"],
    "external_entity": ["spoofing", "repudiation"],
    "data_store": ["tampering", "repudiation", "information_disclosure", "denial_of_service"],
    "data_flow": ["tampering", "information_disclosure", "denial_of_service"],
}
APPLICABLE = {
    "process": ["spoofing", "tampering", "repudiation", "information_disclosure", "denial_of_service",
                "elevation_of_privilege"],
    "external_entity": ["spoofing", "repudiation"],
    "data_store": ["tampering", "information_disclosure", "denial_of_service"],
    "data_flow": ["tampering", "information_disclosure", "denial_of_service"],
}
NA_RATE_WARNING = 0.5
RATIONALE_MIN = 30


def applicable_categories(element: dict) -> list[str]:
    kind = element.get("kind")
    if kind == "data_flow" and not element.get("crosses_boundary"):
        return []
    cats = list(APPLICABLE.get(kind, []))
    if kind == "data_store" and element.get("is_audit_record"):
        cats.append("repudiation")
    return cats


def check_stride_coverage(doc: dict, elements: dict, controls: dict, findings: dict,  # pylint: disable=too-many-branches
                          errors: list[str], warnings: list[str]) -> None:
    """Design section 7 of 0.4.0: completeness and honesty of the STRIDE per element matrix."""
    coverage = doc.get("stride_coverage")
    if coverage is None:
        errors.append("stride_coverage: missing; every assessment needs STRIDE per element coverage (SKILL.md step 8b)")
        return
    if not elements:
        errors.append("stride_coverage: no elements declared; declare elements before covering them (SKILL.md step 3a)")
        return
    seen: dict[tuple[str, str], dict] = {}
    for entry in coverage:
        key = (entry["element_id"], entry["category"])
        where = f"stride_coverage/{entry['element_id']}/{entry['category']}"
        el = elements.get(entry["element_id"])
        if el is None:
            errors.append(f"{where}: element not declared")
            continue
        if entry["category"] not in POSSIBLE.get(el.get("kind"), []):
            errors.append(f"{where}: category does not apply to a {el.get('kind')} element")
            continue
        if key in seen:
            errors.append(f"{where}: duplicate entry")
        seen[key] = entry
        status = entry["status"]
        if status == "finding":
            if not entry.get("finding_ids"):
                errors.append(f"{where}: status finding needs finding_ids")
            for fid in entry.get("finding_ids", []):
                if fid not in findings:
                    errors.append(f"{where}: finding '{fid}' not defined")
                elif entry["category"] not in findings[fid].get("stride", []):
                    warnings.append(f"{where}: finding '{fid}' does not list '{entry['category']}' in its stride; "
                                    "add it so the finding carries every category it covers")
        elif status == "mitigated":
            if not entry.get("control_ids"):
                errors.append(f"{where}: status mitigated needs control_ids")
            for cid in entry.get("control_ids", []):
                ctl = controls.get(cid)
                if ctl is None:
                    errors.append(f"{where}: control '{cid}' not defined")
                elif ctl["status"] == "missing_recommended":
                    errors.append(f"{where}: a missing control cannot mitigate; use status finding or not_assessed")
                elif entry["category"] in {"repudiation", "denial_of_service"} and ctl["mechanism"] == "behavioral":
                    warnings.append(f"{where}: behavioral control '{cid}' cannot restore provenance or limits; "
                                    "see rubric section 5a")
        elif len(entry.get("rationale", "").strip()) < RATIONALE_MIN:
            errors.append(f"{where}: {status} needs a rationale of at least {RATIONALE_MIN} characters")
    required = [(eid, cat) for eid, el in elements.items() for cat in applicable_categories(el)]
    missing = [k for k in required if k not in seen]
    for eid, cat in missing:
        errors.append(f"stride_coverage/{eid}/{cat}: no entry for an applicable category")
    na = sum(1 for k in required if seen.get(k, {}).get("status") == "not_applicable")
    if required and na / len(required) > NA_RATE_WARNING:
        warnings.append(f"stride_coverage: {na} of {len(required)} pairs marked not_applicable; check for checkbox coverage")
    labelled = {fid for fid, f in findings.items() if f.get("stride")}
    referenced = {fid for e in coverage for fid in e.get("finding_ids", [])}
    for fid in sorted(labelled - referenced):
        warnings.append(f"findings/{fid}: has stride labels but no stride_coverage entry references it")


# Values models commonly reach for in the wrong field, with where they belong. Seen in the GPT-5.4 batch:
# third_party and external in peer_trust_level, and NIST_AI_RMF in threat_refs.
GOVERNANCE_FRAMEWORKS = {"NIST_AI_RMF", "NIST_AI_600_1", "ISO_42001", "NIST_SP_800_53", "NIST_COSAIS", "IMDA_MGF_AGENTIC"}


def enum_hint(path: str, value) -> str:
    leaf = path.rsplit("/", 1)[-1]
    if leaf == "peer_trust_level" and value in {"third_party", "external", "outside", "vendor"}:
        return ("; hint: use 'untrusted' for any peer an outside party controls, or 'unknown' "
                "(third_party is a value of subject.trust_domain, not of peer_trust_level)")
    if leaf == "framework" and "/threat_refs/" in f"/{path}/" and value in GOVERNANCE_FRAMEWORKS:
        return "; hint: governance and control frameworks belong in governance_refs, not threat_refs"
    if leaf == "framework" and "/governance_refs/" in f"/{path}/" and value in {
            "OWASP_AGENTIC", "OWASP_LLM_TOP10", "MITRE_ATLAS", "SAFE_MCP", "COSAI"}:
        return "; hint: threat taxonomies and attack techniques belong in threat_refs, not governance_refs"
    return ""


def check(doc: dict, schema: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if Draft202012Validator is not None:
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
            path = "/".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"schema: {path}: {err.message}{enum_hint(path, err.instance)}")
    else:
        warnings.append("schema check skipped: jsonschema is not installed (pip install jsonschema); rubric checks ran")
        if not isinstance(doc, dict):
            return ["structure: the document is not a JSON object"], warnings
        errors += [f"structure: missing required field '{key}'" for key in schema.get("required", []) if key not in doc]
    if errors:
        return errors, warnings  # Semantic checks assume a structurally valid document.

    try:
        _semantic_checks(doc, errors, warnings)
    except (KeyError, TypeError, AttributeError) as exc:
        # Only reachable without jsonschema: the schema check would have caught the malformed field.
        errors.append(f"structure: malformed or missing field ({exc!r}); install jsonschema for a precise message")
    return errors, warnings


def _semantic_checks(doc: dict, errors: list[str], warnings: list[str]) -> None:
    caps = {c["capability_id"]: c for c in doc["capabilities"]}
    inputs = {i["input_id"]: i for i in doc["inputs"]}
    controls = {c["control_id"]: c for c in doc["controls"]}
    elements = {e["element_id"]: e for e in doc.get("elements", [])}
    findings = doc["findings"]

    all_ids: dict[str, str] = {}
    for kind, items, key in (
        ("capability", doc["capabilities"], "capability_id"),
        ("input", doc["inputs"], "input_id"),
        ("control", doc["controls"], "control_id"),
        ("element", doc.get("elements", []), "element_id"),
        ("finding", findings, "finding_id"),
    ):
        for item in items:
            ident = item[key]
            if ident in all_ids:
                errors.append(f"duplicate id '{ident}' ({all_ids[ident]} and {kind})")
            all_ids[ident] = kind

    known_refs = set(caps) | set(inputs) | set(controls) | set(elements) | {doc["subject"]["agent_id"]}
    known_refs |= {p["peer_ref"] for p in doc.get("protocols", [])}
    planned = {i for i, item in {**caps, **inputs, **elements}.items() if item.get("planned")}

    # An element may list its own id in refs (runs do this when a case's stable id is the element
    # itself, such as a store); that is redundant, not wrong, so it is ignored.
    for el in elements.values():
        for ref in el.get("refs", []):
            if ref != el["element_id"] and ref not in known_refs:
                errors.append(f"elements/{el['element_id']}: refs unknown id '{ref}'")

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
            # Same reference set as attack paths, so a control can protect a store or a peer connection.
            if ref not in known_refs or ref in controls:
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
        if f.get("finding_kind") == "property":
            if f.get("attack_path"):
                errors.append(f"{fid}: a property finding has no attack_path; list affected capabilities in affected_refs")
            if not f.get("affected_refs"):
                errors.append(f"{fid}: a property finding needs affected_refs (rubric section 5a)")
            for ref in f.get("affected_refs", []):
                if ref not in known_refs:
                    errors.append(f"{fid}: affected_refs entry '{ref}' not defined in document")
        for step in f.get("attack_path", []):
            if step["ref"] not in known_refs:
                errors.append(f"{fid}: attack_path ref '{step['ref']}' not defined in document")
        for ref in f.get("toxic_combination", []):
            if ref not in known_refs:
                errors.append(f"{fid}: toxic_combination ref '{ref}' not defined in document")
        used_planned = sorted(planned & ({s["ref"] for s in f.get("attack_path", [])} | set(f.get("toxic_combination", []))))
        if used_planned and f["horizon"] == "present":
            errors.append(f"{fid}: present finding references planned element(s) {used_planned}; use horizon forecast")
        adding = {"new_tool", "new_mcp_server", "new_peer_agent", "data_scope_expansion"}
        if used_planned and f.get("forecast") and not adding & set(f["forecast"]["triggers"]):
            warnings.append(f"{fid}: references planned element(s) {used_planned} but no trigger that adds them")
        if RANK[f["residual_risk"]] > RANK[f["inherent_risk"]]:
            errors.append(f"{fid}: residual_risk {f['residual_risk']} exceeds inherent_risk {f['inherent_risk']}")
        fc = f.get("forecast")
        if not fc:
            # Forecasting is PARA's core claim, so every finding carries one (rubric section 6). In the
            # v0.3.2 batch, findings without a forecast fell to 45 percent and nothing caught it.
            errors.append(
                f"{fid}: no forecast block; every finding needs one (rubric section 6). If no trigger "
                "changes the tier, list the triggers considered and set projected_risk equal to residual_risk"
            )
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
                # An error from schema 0.6.0 (rubric 0.3.0); earlier documents keep the warning they targeted.
                below = (f"{fid}: residual '{f['residual_risk']}' is below what path controls can justify "
                         f"('{floor}'); rubric section 5 never allows a residual below the floor")
                (errors if schema_at_least(doc.get("schema_version", "0.0.0"), (0, 6, 0)) else warnings).append(below)
            elif RANK[f["residual_risk"]] > RANK[floor] and not f.get("residual_rationale"):
                warnings.append(
                    f"{fid}: residual '{f['residual_risk']}' is above the rubric floor ('{floor}') with no "
                    "residual_rationale (rubric section 5)"
                )
        if not f.get("recommendations") and RANK[f["residual_risk"]] >= RANK["moderate"]:
            warnings.append(f"{fid}: residual {f['residual_risk']} with no recommendations")
        # A structural fix named only in prose leaves no gap list for reviewers and nothing for a forecast to
        # name. In the GPT-5.4 batch, runs recorded far fewer missing controls than they recommended.
        structural_recs = [r for r in f.get("recommendations", [])
                           if r.get("mechanism") == "structural" and r.get("category") in {"preventive", "containment"}]
        path_refs = set(finding_refs(f)) | set(f.get("toxic_combination", []))
        missing_on_path = [c for c in controls.values()
                           if c["status"] == "missing_recommended" and path_refs & set(c.get("covers", []))]
        if structural_recs and path_refs and not missing_on_path:
            warnings.append(
                f"{fid}: {len(structural_recs)} structural recommendation(s) but no missing_recommended control "
                "covering the attack path; record each recommended control (control_decay.md, missing controls)"
            )
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

    if schema_at_least(doc.get("schema_version", "0.0.0"), (0, 6, 0)):
        check_stride_coverage(doc, elements, controls, {f["finding_id"]: f for f in findings}, errors, warnings)
    for item in list(inputs) + [c for c, cap in caps.items() if cap.get("is_egress")]:
        if elements and not any(item in el.get("refs", []) for el in elements.values()):
            warnings.append(f"elements: {item} appears in no element's refs (stride_agentic.md, minimum elements)")

    if not any("runtime" in lim.lower() for lim in doc["limitations"]):
        errors.append("limitations: must state that the assessment reflects design, not observed runtime behavior")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("assessment", type=Path)
    ap.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    try:
        doc = json.loads(args.assessment.read_text(encoding="utf-8-sig"))
        schema = json.loads(args.schema.read_text(encoding="utf-8-sig"))
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
