"""Explain why runs of the same case disagree on residual risk.

For each case, picks the finding in each run that matches the case's required attack path (or the
highest inherent finding when the case has none), then shows the residual each run gave, the floor the
rubric credits allow, and every control the run placed on that path with the attributes that decide
its credit.

Usage:
  python evals/compare_residuals.py                       cases 01, 03, 04, 10, 11
  python evals/compare_residuals.py --case 04_third_party_mcp_tool_poisoning
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "para" / "scripts"))
from validate import RANK, residual_floor  # noqa: E402

EVALS = ROOT / "evals"
RUN_GLOB = "run_[0-9][0-9][0-9].json"
DEFAULT_CASES = [
    "01_support_triage", "03_issue_fixer_self_config", "04_third_party_mcp_tool_poisoning",
    "10_backtest_github_mcp", "11_backtest_supabase_mcp",
]


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def pick_finding(doc: dict, required_paths: list[list[str]]) -> dict | None:
    present = [f for f in doc.get("findings", []) if f.get("horizon") == "present"]
    for req in required_paths:
        for f in present:
            refs = [s.get("ref") for s in f.get("attack_path", [])]
            if all(r in refs for r in req):
                return f
    if present:
        return max(present, key=lambda f: RANK.get(f.get("inherent_risk"), -1))
    return None


def credit_step(ctl: dict, gate_ids: set[str]) -> str:
    """Which rubric section 5 step this control earns credit at, mirroring validate.residual_floor."""
    if ctl.get("status") == "missing_recommended":
        return "none (missing)"
    if ctl["control_id"] in gate_ids:
        return f"step 2 gate ({ctl.get('approval_review_mode', 'no review mode')})"
    if ctl.get("category") not in {"preventive", "containment"}:
        return f"none ({ctl.get('category')})"
    if (ctl.get("severs_path") and ctl.get("mechanism") == "structural"
            and ctl.get("capability_dependence") == "independent" and ctl.get("category") == "preventive"):
        return "step 1 severs"
    if ctl.get("mechanism") == "structural" and ctl.get("capability_dependence") != "dependent":
        return "step 3"
    return "step 4"


def describe_run(path: Path, doc: dict, required_paths: list[list[str]]) -> list[str]:
    f = pick_finding(doc, required_paths)
    if not f:
        return [f"  {path.name}: no present finding"]
    caps = {c["capability_id"]: c for c in doc.get("capabilities", [])}
    controls = {c["control_id"]: c for c in doc.get("controls", [])}
    refs = {s.get("ref") for s in f.get("attack_path", [])}
    gate_ids = {caps[r].get("approval_gate_ref") for r in refs if r in caps} - {None}
    element_ids = {e.get("element_id") for e in doc.get("elements", [])}
    peers = {p.get("peer_ref") for p in doc.get("protocols", [])}
    try:
        floor = residual_floor(f, caps, controls)
    except (KeyError, TypeError):
        floor = "?"
    lines = [
        f"  {path.name}: inherent={f.get('inherent_risk')} residual={f.get('residual_risk')} "
        f"rubric_floor={floor} path={[s.get('ref') for s in f.get('attack_path', [])]}"
    ]
    on_path = [c for c in controls.values()
               if refs & set(c.get("covers", [])) or c["control_id"] in gate_ids]
    off_path_relevant = [c for c in controls.values() if c not in on_path
                         and set(c.get("covers", [])) & (element_ids | peers)]
    for c in on_path:
        via = sorted(refs & set(c.get("covers", []))) or ["approval_gate_ref"]
        lines.append(
            f"      ON  {c['control_id']}: {credit_step(c, gate_ids)} | {c.get('category')}, {c.get('mechanism')}, "
            f"{c.get('capability_dependence')}, status={c.get('status')} | via {via}"
        )
    for c in off_path_relevant:
        lines.append(
            f"      OFF {c['control_id']}: covers only elements or peers {sorted(set(c.get('covers', [])))} "
            f"| would earn {credit_step(c, gate_ids)} if it were on the path"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", action="append", help="case_id; repeatable. Default: cases 01, 03, 04, 10, 11")
    ap.add_argument("--runs-dir", type=Path, default=EVALS / "runs", help="folder of runs (default evals/runs)")
    args = ap.parse_args(argv)
    for case_id in args.case or DEFAULT_CASES:
        exp = load(EVALS / "expected" / f"{case_id}.expected.json") or {}
        print(f"## {case_id}  expected residual {exp.get('rating', {}).get('residual')}")
        for path in sorted((args.runs_dir / case_id).glob(RUN_GLOB)):
            doc = load(path)
            if not isinstance(doc, dict) or "_parse_error" in doc:
                print(f"  {path.name}: not parseable")
                continue
            try:
                print("\n".join(describe_run(path, doc, exp.get("required_paths", []))))
            except (KeyError, TypeError, AttributeError) as exc:
                print(f"  {path.name}: malformed ({exc!r})")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
