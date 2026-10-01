"""Score PARA outputs against expected results and measure run to run consistency.

Layout:
  evals/cases/<case_id>.md                  agent design given to the assessor
  evals/expected/<case_id>.expected.json    required paths, tier ranges
  evals/runs/<case_id>/*.json               one assessment per run (produced by the skill)

Expected file keys: rating ranges, required_paths, required_toxic_combinations,
required_failing_controls_by_capability, required_threat_ids, required_triggers,
required_evidence_substrings, required_forecast_findings_min, false_positive_threshold,
required_stride_categories.

Usage:
  python evals/run_consistency.py                       score every case that has runs
  python evals/run_consistency.py --case 01_support_triage
  python evals/run_consistency.py --report evals/RESULTS.md   also write a publishable summary
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
# Assessment files only; run_NNN.meta.json sidecars hold token usage and are not scored.
RUN_GLOB = "run_[0-9][0-9][0-9].json"


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

    # STRIDE categories that must appear on at least one finding (coverage cases 12 and 13).
    stride_found = {s for f in findings for s in f.get("stride", [])}
    req_stride = exp.get("required_stride_categories", [])
    hits += len(set(req_stride) & stride_found)

    # Evidence checks: for example, the assessor must quote injected text instead of obeying it (case 09).
    evidence_text = " ".join(
        f"{e.get('locator', '')} {e.get('observation', '')}" for f in findings for e in f.get("evidence", [])
    ).lower()
    req_evidence = exp.get("required_evidence_substrings", [])
    hits += sum(s.lower() in evidence_text for s in req_evidence)

    # Forecast only designs must still produce forecast findings (case 08).
    min_forecast = exp.get("required_forecast_findings_min", 0)
    if min_forecast:
        hits += sum(1 for f in findings if f["horizon"] == "forecast") >= min_forecast

    total = (
        len(req_paths) + len(req_combos) + len(exp.get("required_failing_controls_by_capability", {}))
        + len(exp.get("required_threat_ids", [])) + len(exp.get("required_triggers", []))
        + len(req_evidence) + (1 if min_forecast else 0) + len(req_stride)
    )

    fp = 0
    if "false_positive_threshold" in exp:
        threshold = RANK[exp["false_positive_threshold"]]
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


def invalid_result(reason: str) -> dict:
    return {
        "valid": False, "errors": 1, "warnings": 0, "error_detail": reason,
        "rating": {k: None for k in FIELDS}, "in_range": {k: False for k in FIELDS},
        "recall": 0.0, "false_positives": 0,
    }


def score_file(path: Path, exp: dict, schema: dict) -> dict:
    """Score one run file. Unparseable or structurally broken output counts as an invalid run, never
    as a skipped one, so failures cannot quietly raise the averages."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return invalid_result(f"unreadable: {exc}")
    if not isinstance(doc, dict) or "_parse_error" in doc:
        return invalid_result(str(doc.get("_parse_error", "not an object")) if isinstance(doc, dict) else "not an object")
    try:
        return score_run(doc, exp, schema)
    except (KeyError, TypeError, AttributeError) as exc:
        return invalid_result(f"malformed: {exc!r}")


def case_stats(results: list[dict]) -> dict:
    n = len(results)
    stats = {"runs": n, "valid": sum(r["valid"] for r in results) / n,
             "recall": sum(r["recall"] for r in results) / n,
             "false_positives": sum(r["false_positives"] for r in results)}
    for k in FIELDS:
        counts = Counter(r["rating"][k] for r in results)
        mode, mode_n = counts.most_common(1)[0]
        stats[k] = {"mode": mode, "agreement": mode_n / n, "in_range": sum(r["in_range"][k] for r in results) / n}
    return stats


def mean_output_tokens(runs_dir: Path) -> float | None:
    """Mean output tokens across run_NNN.meta.json sidecars written by run_skill.py, if any."""
    counts = []
    for meta_path in runs_dir.glob("run_[0-9][0-9][0-9].meta.json"):
        try:
            value = json.loads(meta_path.read_text(encoding="utf-8")).get("output_tokens")
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, int):
            counts.append(value)
    return sum(counts) / len(counts) if counts else None


def markdown_report(stats: dict[str, dict], kinds: dict[str, str], meta: dict) -> str:
    """Summary table suitable for publishing in the README or a release."""
    lines = ["# PARA eval results", "",
             "Validator clean means the assessment parsed, matched the schema, and passed every rubric "
             "consistency check in scripts/validate.py with zero errors.", ""]
    if meta:
        lines += [f"- {k}: {v}" for k, v in meta.items()] + [""]
    head = "| Case | Kind | Runs | Validator clean | Recall | " + " | ".join(
        f"{k.capitalize()} agreement / in range" for k in FIELDS) + " | False positives |"
    lines += [head, "|" + "---|" * (6 + len(FIELDS))]
    for case_id, s in stats.items():
        cells = " | ".join(f"{s[k]['agreement']:.0%} / {s[k]['in_range']:.0%}" for k in FIELDS)
        lines.append(f"| {case_id} | {kinds.get(case_id, '')} | {s['runs']} | {s['valid']:.0%} | "
                     f"{s['recall']:.0%} | {cells} | {s['false_positives']} |")
    if stats:
        total_runs = sum(s["runs"] for s in stats.values())
        def weighted(key):
            return sum(s[key] * s["runs"] for s in stats.values()) / total_runs
        lines += ["", f"Overall: {total_runs} runs, validator clean {weighted('valid'):.0%}, "
                      f"mean recall {weighted('recall'):.0%}."]
        tokens = [s["mean_output_tokens"] for s in stats.values() if s.get("mean_output_tokens")]
        if tokens:
            lines.append(f"Mean output tokens per assessment: {sum(tokens) / len(tokens):,.0f}.")
        backtests = {c: s for c, s in stats.items() if kinds.get(c) == "backtest"}
        if backtests:
            lines += ["", "Backtests (would PARA have flagged the incident path and failing control beforehand):"]
            lines += [f"- {c}: recall {s['recall']:.0%}, inherent in range {s['inherent']['in_range']:.0%}"
                      for c, s in backtests.items()]
    return "\n".join(lines) + "\n"


def run_runner(template: str, case: Path, out_dir: Path, n: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    start = len(list(out_dir.glob(RUN_GLOB)))
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
        lines.append(f"  {k:9} mode={str(mode):9} agreement={agree:.2f} in_range={in_range:.2f} dist={dict(counts)}{flag}")
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
    ap.add_argument("--report", type=Path, help="write a Markdown summary table to this file")
    args = ap.parse_args(argv)

    schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
    expected_files = sorted((EVALS / "expected").glob("*.expected.json"))
    if args.case:
        expected_files = [p for p in expected_files if p.name == f"{args.case}.expected.json"]
        if not expected_files:
            print(f"error: no expected file for case '{args.case}'", file=sys.stderr)
            return 2

    all_ok, report, dump, stats, kinds = True, [], {}, {}, {}
    for exp_path in expected_files:
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        case_id = exp["case_id"]
        runs_dir = EVALS / "runs" / case_id
        if args.runner:
            run_runner(args.runner, EVALS / "cases" / f"{case_id}.md", runs_dir, args.n)
        run_files = sorted(runs_dir.glob(RUN_GLOB)) if runs_dir.exists() else []
        if not run_files:
            report.append(f"## {case_id}: no runs in {runs_dir.relative_to(ROOT)}")
            continue
        results = [score_file(p, exp, schema) for p in run_files]
        dump[case_id] = results
        stats[case_id], kinds[case_id] = case_stats(results), exp.get("kind", "")
        stats[case_id]["mean_output_tokens"] = mean_output_tokens(runs_dir)
        lines, ok = summarize(case_id, results, args.min_agreement)
        report += lines
        all_ok &= ok

    print("\n".join(report))
    if args.json:
        args.json.write_text(json.dumps(dump, indent=2), encoding="utf-8")
    if args.report:
        manifest_path = EVALS / "runs" / "manifest.json"
        meta = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        args.report.write_text(markdown_report(stats, kinds, meta), encoding="utf-8")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
