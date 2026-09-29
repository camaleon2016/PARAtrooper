"""Render a PARA assessment as a Markdown summary.

Usage: python scripts/render_report.py <assessment.json> [--view developer|reviewer|both] [-o OUT.md]

Developer view: findings and controls ranked by how soon each control decays.
Reviewer view: rating, evidence, forecast assumptions, governance and treatment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RANK = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
DECAY_ORDER = {"dependent": 0, "partially_dependent": 1, "independent": 2}
PRIORITY = {"p1": 0, "p2": 1, "p3": 2}


def md_escape(text: str) -> str:
    """Escape untrusted text for Markdown prose and table cells.

    Assessed artifacts may contain hostile text. Raw HTML such as <img src=...> would let a
    quoted artifact trigger an outbound fetch in any viewer that renders HTML, so angle brackets
    and ampersands are entity encoded. Pipes, brackets, and backticks are escaped so the text
    cannot break tables, create links or images, or open code spans.
    """
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for ch in ("\\", "|", "[", "]", "`", "*", "_"):
        text = text.replace(ch, "\\" + ch)
    return text.replace("\r", " ").replace("\n", " ")


def md_code(text: str) -> str:
    """Render an identifier as an inline code span. Backslash escapes do not work inside code
    spans, so backticks and line breaks are replaced rather than escaped."""
    return "`" + str(text).replace("`", "'").replace("\r", " ").replace("\n", " ") + "`"


def plural_verb(count: int, singular: str, plural: str) -> str:
    return singular if count == 1 else plural


def headline(doc: dict) -> list[str]:
    r = doc["rating"]
    s = doc["subject"]
    return [
        f"# PARA assessment: {md_escape(s['name'])} ({md_code(s['agent_id'])})",
        "",
        "| Inherent | Residual | Forecast |",
        "|---|---|---|",
        f"| **{r['inherent']}** | **{r['residual']}** | **{r['forecast']}** |",
        "",
        md_escape(r["rationale"]),
        "",
    ]


def approval_note(control: dict) -> str:
    mode = control.get("approval_review_mode")
    return f" (approver sees {mode.replace('_', ' ')})" if mode else ""


def developer_view(doc: dict) -> list[str]:
    out = ["## Developer view", "", "### Controls, soonest to decay first", ""]
    out += ["| Control | Mechanism | Dependence | Status | Covers | Why it decays |", "|---|---|---|---|---|---|"]
    # Approval gates show how the approver sees the action, since summary review decays with capability.
    for c in sorted(doc["controls"], key=lambda c: (DECAY_ORDER[c["capability_dependence"]], c["control_id"])):
        out.append(
            f"| {md_escape(c['name'])}{approval_note(c)} | {c['mechanism']} | {c['capability_dependence']} | {c['status']} "
            f"| {md_escape(', '.join(c.get('covers', [])))} | {md_escape(c.get('decay_rationale', ''))} |"
        )
    out += ["", "### Fix list", ""]
    recs = [
        (PRIORITY[r["priority"]], -RANK[f["residual_risk"]], f["finding_id"], r)
        for f in doc["findings"]
        for r in f.get("recommendations", [])
        if r.get("audience", "both") in {"developer", "both"}
    ]
    for _, _, fid, r in sorted(recs, key=lambda x: x[:3]):
        out.append(
            f"- **{r['priority'].upper()}** ({r['mechanism']} {r['category']}) {md_escape(r['action'])} ({md_code(fid)})"
        )
    if not recs:
        out.append("- None.")
    return out + [""]


def reviewer_view(doc: dict) -> list[str]:
    a = doc["assessment"]
    out = [
        "## Reviewer view",
        "",
        f"- Assessment {md_code(a['assessment_id'])} at {a['assessed_at']}, reason: {a.get('assessment_reason', 'n/a')}",
        f"- Assessor: {a['assessor']['kind']} {a['assessor']['version']}, rubric {a['assessor'].get('rubric_version', 'n/a')}"
        + (f", model {a['assessor']['model']}" if a["assessor"].get("model") else ""),
        f"- Evidence basis: {a['evidence_basis']}",
        f"- Autonomy: {doc['autonomy']['level']}",
        "",
    ]
    for horizon in ("present", "forecast"):
        fs = sorted((f for f in doc["findings"] if f["horizon"] == horizon), key=lambda f: -RANK[f["residual_risk"]])
        out += [f"### {horizon.capitalize()} findings", ""]
        if not fs:
            out += ["None.", ""]
        for f in fs:
            out.append(f"#### {md_escape(f['title'])} ({md_code(f['finding_id'])})")
            out.append("")
            out.append(
                f"Inherent **{f['inherent_risk']}**, residual **{f['residual_risk']}**, confidence {f['confidence']}"
                + (f", likelihood {f['likelihood']}" if f.get("likelihood") else "")
                + (f", consequence {f['consequence']}" if f.get("consequence") else "")
            )
            if f.get("attack_path"):
                out.append("")
                out.append("Path: " + " → ".join(md_code(s["ref"]) for s in f["attack_path"]))
            out += ["", "Evidence:"]
            out += [f"- {md_code(e['locator'])}: {md_escape(e['observation'])}" for e in f["evidence"]]
            fc = f.get("forecast")
            if fc:
                failing = fc["failing_controls"]
                subject = ", ".join(md_code(c) for c in failing) or "no listed controls"
                verb = plural_verb(len(failing), "fails", "fail")
                out += [
                    "",
                    f"Forecast: if **{', '.join(fc['triggers'])}**, then {subject} {verb} and the tier becomes "
                    f"**{fc['projected_risk']}**.",
                ]
                if fc.get("watch_signal"):
                    out.append(f"Watch: {md_escape(fc['watch_signal'])}")
            refs = [f"{t['framework']} {t['id']}" for t in f.get("threat_refs", [])]
            refs += [f"{g['framework']} {g['id']}" for g in f.get("governance_refs", [])]
            if refs:
                out += ["", "Refs: " + md_escape("; ".join(refs))]
            if f.get("treatment"):
                t = f["treatment"]
                out += ["", f"Treatment: {t['option']}" + (f", owner {md_escape(t['owner'])}" if t.get("owner") else "")
                        + (f", approved by {md_escape(t['approved_by'])}" if t.get("approved_by") else "")]
            out.append("")
    out += ["### Limitations", ""] + [f"- {md_escape(l)}" for l in doc["limitations"]] + [""]
    return out


def render(doc: dict, view: str) -> str:
    lines = headline(doc)
    if view in {"developer", "both"}:
        lines += developer_view(doc)
    if view in {"reviewer", "both"}:
        lines += reviewer_view(doc)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("assessment", type=Path)
    ap.add_argument("--view", choices=["developer", "reviewer", "both"], default="both")
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args(argv)
    doc = json.loads(args.assessment.read_text(encoding="utf-8"))
    text = render(doc, args.view)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
