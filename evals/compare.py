"""Compare two eval folders case by case: python evals/compare.py"""
import json, sys
from pathlib import Path
sys.path[:0] = ["skills/para/scripts", "evals"]
import run_consistency as rc
from validate import DEFAULT_SCHEMA
schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8-sig"))
PAIRS = [("GPT-5.4 with repair", "evals/runs-gpt-54-v041-repair", "evals/runs-gpt-54-v042"),
         ("Claude", "evals/runs-claude-v040", "evals/runs-claude-v042"),
         ("Gemini", None, "evals/runs-gemini-v042")]
def stats(folder, case):
    if not folder: return None
    exp = json.loads(Path(f"evals/expected/{case}.expected.json").read_text(encoding="utf-8-sig"))
    files = sorted(Path(folder, case).glob(rc.RUN_GLOB))
    return rc.case_stats([rc.score_file(p, exp, schema) for p in files]) if files else None
cases = sorted(p.stem for p in Path("evals/cases").glob("*.md"))
fmt = lambda s, k, pct=True: "n/a" if not s or s.get(k) is None else (f"{s[k]:.0%}" if pct else str(s[k]))
for name, before, after in PAIRS:
    if not Path(after).exists(): continue
    print(f"\n== {name}: {'before -> ' if before else ''}v0.4.2")
    print("case".ljust(34), "recall".rjust(14), "main path agr".rjust(15), "false pos".rjust(11), "clean".rjust(13))
    B, A = {}, {}
    for c in cases:
        b, a = stats(before, c), stats(after, c)
        B[c], A[c] = b, a
        arrow = lambda k, pct=True: f"{fmt(b,k,pct)} -> {fmt(a,k,pct)}" if before else fmt(a, k, pct)
        print(c[:34].ljust(34), arrow("recall").rjust(14), arrow("main_path_residual").rjust(15),
              arrow("false_positives", False).rjust(11), arrow("valid").rjust(13))
    low = {c[:2]: f"{A[c]['main_path_residual']:.0%}" for c in cases if A[c] and A[c].get("main_path_residual") is not None and A[c]["main_path_residual"] < 0.8}
    core = [c for c in cases if c[:2] <= "13" and A[c]]
    mean = lambda d: sum(d[c]["recall"] for c in core if d.get(c)) / max(1, sum(1 for c in core if d.get(c)))
    held = [c for c in cases if c.startswith(("14", "15", "16")) and A[c]]
    print(f"Recall 01 to 13: {mean(A):.0%}" + (f" (was {mean(B):.0%})" if before else ""),
          f"| held out: {sum(A[c]['recall'] for c in held) / max(1, len(held)):.0%}",
          f"| false positives: {sum(A[c]['false_positives'] for c in cases if A[c])}")
    print("Main path agreement 80% or more everywhere:", not low, low or "")
