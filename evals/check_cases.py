"""Check that every eval case and expected file agree with each other and with the schema.

Usage: python evals/check_cases.py
Exit code 0 = consistent, 1 = problems found.

This does not run the skill. It catches drift: an expected file that names an id the case never
defines, a trigger or tier the schema does not allow, a case with no expected file, or a MITRE ATLAS
or SAFE-MCP id that does not exist in the pinned edition under references/data/.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
SCHEMA = json.loads((ROOT / "schema" / "assessment.schema.json").read_text(encoding="utf-8-sig"))
TIERS = set(SCHEMA["$defs"]["tier"]["enum"])
TRIGGERS = set(SCHEMA["$defs"]["forecast_trigger"]["enum"])
KINDS = {"vulnerable", "clean", "edge", "forecast", "backtest", "coverage"}
STRIDE = set(SCHEMA["$defs"]["stride"]["enum"])
ASI_ID = re.compile(r"^ASI(0[1-9]|10)$")
FIELDS = ("inherent", "residual", "forecast")
DATA = ROOT / "references" / "data"
ATLAS_ID = re.compile(r"\bAML\.T\d{4}(?:\.\d{3})?\b")
SAFE_ID = re.compile(r"\bSAFE-T\d{4}(?:\.\d{3})?\b")
# Files whose framework ids must exist in the pinned editions. The CHANGELOG is exempt because it
# records retired ids on purpose.
ID_SCAN = ["references/*.md", "examples/*.json", "evals/cases/*.md", "evals/expected/*.json", "SKILL.md"]


def load_ids(name: str) -> set[str]:
    lines = (DATA / name).read_text(encoding="utf-8").splitlines()
    return {line.split("\t", 1)[0] for line in lines if line and not line.startswith("#")}


def check_framework_ids() -> list[str]:
    """Every ATLAS and SAFE-MCP id cited in the repo must exist in the pinned edition."""
    atlas, safe = load_ids("atlas_ids_2026.09.tsv"), load_ids("safe_mcp_ids.tsv")
    retired_note = "formerly AML.T0104"
    problems: list[str] = []
    for pattern in ID_SCAN:
        for path in sorted(ROOT.glob(pattern)):
            text = path.read_text(encoding="utf-8").replace(retired_note, "")
            rel = path.relative_to(ROOT).as_posix()
            problems += [f"{rel}: {i} not in ATLAS 2026.09" for i in sorted(set(ATLAS_ID.findall(text)) - atlas)]
            problems += [f"{rel}: {i} not in pinned SAFE-MCP catalog" for i in sorted(set(SAFE_ID.findall(text)) - safe)]
    return problems


def stable_ids(case_text: str) -> set[str]:
    return set(re.findall(r"^\|[^|]*\|\s*`([^`]+)`\s*\|\s*$", case_text, flags=re.MULTILINE))


def check_case(exp_path: Path) -> list[str]:
    problems: list[str] = []
    exp = json.loads(exp_path.read_text(encoding="utf-8-sig"))
    case_id = exp.get("case_id", "")
    where = exp_path.name
    if exp_path.name != f"{case_id}.expected.json":
        problems.append(f"{where}: case_id '{case_id}' does not match the file name")
    case_path = EVALS / "cases" / f"{case_id}.md"
    if not case_path.exists():
        return problems + [f"{where}: no case file {case_path.relative_to(ROOT)}"]
    ids = stable_ids(case_path.read_text(encoding="utf-8"))
    if not ids:
        problems.append(f"{case_path.name}: no stable ids table")

    if exp.get("kind") not in KINDS:
        problems.append(f"{where}: kind '{exp.get('kind')}' not in {sorted(KINDS)}")
    for field in FIELDS:
        allowed = exp.get("rating", {}).get(field)
        if not allowed or not set(allowed) <= TIERS:
            problems.append(f"{where}: rating.{field} must be a non empty list of tiers")

    referenced = [r for p in exp.get("required_paths", []) for r in p]
    referenced += [r for c in exp.get("required_toxic_combinations", []) for r in c]
    referenced += list(exp.get("required_failing_controls_by_capability", {}))
    for ref in referenced:
        if ref not in ids:
            problems.append(f"{where}: '{ref}' is not in the case's stable ids table")

    for tid in exp.get("required_threat_ids", []):
        if not ASI_ID.match(tid):
            problems.append(f"{where}: threat id '{tid}' is not an OWASP ASI id")
    for trig in exp.get("required_triggers", []):
        if trig not in TRIGGERS:
            problems.append(f"{where}: trigger '{trig}' is not in the schema's forecast_trigger enum")
    for cat in exp.get("required_stride_categories", []):
        if cat not in STRIDE:
            problems.append(f"{where}: STRIDE category '{cat}' is not in the schema's stride enum")
    threshold = exp.get("false_positive_threshold")
    if threshold is not None and threshold not in TIERS:
        problems.append(f"{where}: false_positive_threshold '{threshold}' is not a tier")
    return problems


def main() -> int:
    expected = sorted((EVALS / "expected").glob("*.expected.json"))
    problems: list[str] = []
    for exp_path in expected:
        problems += check_case(exp_path)
    covered = {p.name.removesuffix(".expected.json") for p in expected}
    for case_path in sorted((EVALS / "cases").glob("*.md")):
        if case_path.stem not in covered:
            problems.append(f"{case_path.name}: no expected file")
    problems += check_framework_ids()
    for p in problems:
        print(f"ERROR   {p}")
    print(f"{'OK' if not problems else 'FAILED'}: {len(expected)} cases checked, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
