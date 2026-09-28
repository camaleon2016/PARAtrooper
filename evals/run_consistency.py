"""Score PARA outputs against expected results and measure run to run consistency.

Layout:
  evals/cases/<case_id>.md                  agent design given to the assessor
  evals/expected/<case_id>.expected.json    required paths, tier ranges
  evals/runs/<case_id>/*.json               one assessment per run (produced by the skill)

Usage:
  python evals/run_consistency.py                       score every case that has runs
  python evals/run_consistency.py --case 01_support_triage
  python evals/run_consistency.py --case 01_support_triage -n 5 --runner "my-agent-cli --input {case} --output {out}"

The runner is optional. It is executed without a shell, once per run, with {case} and {out} substituted.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate import DEFAULT_SCHEMA, RANK, check  # noqa: E402

EVALS = ROOT / "evals"
FIELDS = ("inherent", "residual", "forecast")


def is_subsequence(needle: list[str], hay: list[str]) -> bool:
    it = iter(hay)
    return all(x in it for x in needle)


def score_run(doc: dict, exp: dict, schema: dict) -> dict:
    errors, warnings = check(doc, schema)
    findings = doc.get("findings", [])
    controls = {c["control_id"]: c for c in doc.get("controls", [])}
    paths = [[s["ref"] for s in f.get("attack_path", [])] for f in findings]
    combos = [set(f.get("toxic_combination", [])) for f in findings]
    threat_ids = {t["id"] for f in findings for t in f.get("threat_refs", [])}
    triggers = {t for f in findings if f.get("forecast") for t in f["forecast"]["triggers"]}
    failing = [controls[c] for f in findings if f.get("forecast") for c in f["forecast"]["failing_controls"] if c in controls]

    req_paths = exp.get("required_paths", [])
    req_combos = exp.get("required_toxic_combinations", [])
    hits = sum(any(is_subsequence(p, got) for got in paths) for p in req_paths)
    hits += sum(any(set(c) <= got for got in combos) for c in req_combos)
    for cap_id, want in exp.get("required_failing_controls_by_capability", {}).items():
        hits += any(cap_id in c.get("covers", []) and all(c.get(k) == v for k, v in want.items()) for c in failing)
    hits += len(set(exp.get("required_threat_ids", [])) & threat_ids)
    hits += len(set(exp.get("required_triggers", [])) & triggers)
    total = (
        len(req_paths) + len(req_combos) + len(exp.get("required_failing_controls_by_capability", {}))
        + len(exp.get("required_threat_ids", [])) + len(exp.get("required_triggers", []))
    )

    fp = 0
    if exp.get("kind") == "clean":
        threshold = RANK[exp.get("false_positive_threshold", "moderate")]
        fp = sum(1 for f in findings if f["horizon"] == "present" and RANK[f["residual_risk"]] >= threshold)

    rating = doc.get("rating", {})
    in_range = {k: rating.get(k) in exp["rating"][k] for k in FIELDS}
    return {
        "valid": not errors,
        "errors": len(errors),
        "warnings": len(warnings),
        "rating": {k: rating.get(k) for k in FIELDS},
        "in_range": in_range,
        "recall": hits / total if total else 1.0,
        "false_positives": fp,
    }


def run_runner(template: str, case: Path, out_dir: Path, n: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    start = len(list(out_dir.glob("*.json")))
    for i in range(start, start + n):
        out = out_dir / f"run_{i:03d}.json"
        cmd = [part.format(case=str(case), out=str(out)) for part in shlex.split(template, posix=True)]
        subprocess.run(cmd, check=True)


def summarize(case_id: str, results: list[dict], min_agreement: float) -> tuple[list[str], bool]:
    n = len(results)
    lines = [f"## {case_id} ({n} runs)"]
    ok = True
    for k in FIELDS:
        counts = Counter(r["rating"][k] for r in results)
        mode, mode_n = counts.most_common(1)[0]
        agree = mode_n / n
        in_range = sum(r["in_range"][k] for r in results) / n
        flag = "" if agree >= min_agreement and in_range == 1 else "  <-- below target"
        ok &= not flag
        lines.append(f"  {k:9} mode={mode:9} agreement={agree:.2f} in_range={in_range:.2f} dist={dict(counts)}{flag}")
    recall = sum(r["recall"] for r in results) / n
    valid = sum(r["valid"] for r in results) / n
    fp = sum(r["false_positives"] for r in results)
    ok &= valid == 1 and fp == 0
    lines.append(f"  recall={recall:.2f} schema_valid={valid:.2f} false_positives={fp}")
    return lines, ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", help="case_id; default is every case under evals/expected")
    ap.add_argument("-n", type=int, default=5, help="runs to generate when --runner is given")
    ap.add_argument("--runner", help="command template with {case} and {out}; executed without a shell")
    ap.add_argument("--min-agreement", type=float, default=0.8)
    ap.add_argument("--json", type=Path, help="write per run scores to this file")
    args = ap.parse_args(argv)

    schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
    expected_files = sorted((EVALS / "expected").glob("*.expected.json"))
    if args.case:
        expected_files = [p for p in expected_files if p.name == f"{args.case}.expected.json"]
        if not expected_files:
            print(f"error: no expected file for case '{args.case}'", file=sys.stderr)
            return 2

    all_ok, report, dump = True, [], {}
    for exp_path in expected_files:
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        case_id = exp["case_id"]
        runs_dir = EVALS / "runs" / case_id
        if args.runner:
            run_runner(args.runner, EVALS / "cases" / f"{case_id}.md", runs_dir, args.n)
        run_files = sorted(runs_dir.glob("*.json")) if runs_dir.exists() else []
        if not run_files:
            report.append(f"## {case_id}: no runs in {runs_dir.relative_to(ROOT)}")
            continue
        results = [score_run(json.loads(p.read_text(encoding="utf-8")), exp, schema) for p in run_files]
        dump[case_id] = results
        lines, ok = summarize(case_id, results, args.min_agreement)
        report += lines
        all_ok &= ok

    print("\n".join(report))
    if args.json:
        args.json.write_text(json.dumps(dump, indent=2), encoding="utf-8")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
