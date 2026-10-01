"""Tally run outcomes and the most common validator errors across evals/runs.

Usage: python evals/tally_runs.py            summary plus the 15 most common error kinds
       python evals/tally_runs.py --all      also list every failing run and its first error

Use this after a batch to see why runs were not validator clean: truncation, unparseable output, or
specific rubric and schema rules. Error messages are normalized (ids and values removed) so the same
rule failing in different runs is counted once per kind.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from validate import DEFAULT_SCHEMA, check  # noqa: E402

RUNS = ROOT / "evals" / "runs"
RUN_GLOB = "run_[0-9][0-9][0-9].json"


def error_kind(message: str) -> str:
    """Collapse one validator message to its rule: drop the location prefix, ids, and values."""
    text = message.split(": ", 1)[1] if ": " in message else message
    text = re.sub(r"'[^']*'", "'<v>'", text)
    text = re.sub(r"\b[\w-]+\.[\w.-]+\b", "<id>", text)
    return re.sub(r"\d+", "<n>", text)


def classify(path: Path, schema: dict) -> tuple[str, list[str]]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "unreadable", [str(exc)]
    if not isinstance(doc, dict):
        return "unparseable", ["not an object"]
    if "_parse_error" in doc:
        return ("truncated" if "truncated" in doc["_parse_error"] else "unparseable"), [doc["_parse_error"]]
    try:
        errors, _ = check(doc, schema)
    except (KeyError, TypeError, AttributeError) as exc:
        return "malformed", [repr(exc)]
    return ("validator errors" if errors else "clean"), errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="list every failing run")
    args = ap.parse_args(argv)
    schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    outcomes, kinds, by_case = Counter(), Counter(), {}
    for path in sorted(RUNS.glob(f"*/{RUN_GLOB}")):
        outcome, errors = classify(path, schema)
        outcomes[outcome] += 1
        by_case.setdefault(path.parent.name, Counter())[outcome] += 1
        if outcome == "validator errors":
            kinds.update({error_kind(e) for e in errors})
        if args.all and outcome != "clean":
            print(f"{path.relative_to(ROOT).as_posix()}: {outcome}: {errors[0] if errors else ''}")

    print("Outcomes:", dict(outcomes))
    for case_id, counts in by_case.items():
        if counts["clean"] != sum(counts.values()):
            print(f"  {case_id}: {dict(counts)}")
    if kinds:
        print("\nMost common validator error kinds (runs affected):")
        for kind, count in kinds.most_common(15):
            print(f"  {count:3}  {kind}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
