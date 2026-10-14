import json, sys
from pathlib import Path
sys.path[:0] = ["skills/para/scripts", "evals"]
import run_consistency as rc
from validate import DEFAULT_SCHEMA
schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8-sig"))
def stats(folders, case):
    exp = json.loads(Path(f"evals/expected/{case}.expected.json").read_text(encoding="utf-8-sig"))
    files = [p for f in folders for p in sorted(Path(f, case).glob(rc.RUN_GLOB))]
    return rc.case_stats([rc.score_file(p, exp, schema) for p in files]) if files else None
cases = sorted(p.stem for p in Path("evals/cases").glob("*.md"))
models = [("GPT-5.4", ["evals/runs-gpt-54-v035", "evals/runs-gpt-54-v035-heldout"], ["evals/runs-gpt-54-v040"]),
          ("Claude", ["evals/runs-claude-v035", "evals/runs-claude-v035-heldout"], ["evals/runs-claude-v040"])]
for model, base, treat in models:
    if not Path(treat[0]).exists():
        continue
    print(f"\n== {model}: v0.3.5 -> v0.4.0")
    print("case".ljust(34), "recall".rjust(14), "main path agr".rjust(15), "false pos".rjust(11))
    b_all, t_all = {}, {}
    for c in cases:
        b, t = stats(base, c), stats(treat, c)
        b_all[c], t_all[c] = b, t
        fmt = lambda s, k, pct=True: "n/a" if not s or s.get(k) is None else (f"{s[k]:.0%}" if pct else str(s[k]))
        print(c[:34].ljust(34), f"{fmt(b,'recall')} -> {fmt(t,'recall')}".rjust(14),
              f"{fmt(b,'main_path_residual')} -> {fmt(t,'main_path_residual')}".rjust(15),
              f"{fmt(b,'false_positives',False)} -> {fmt(t,'false_positives',False)}".rjust(11))
    core = [c for c in cases if c[:2] <= "11"]
    cov = [c for c in cases if c.startswith(("12", "13", "15"))]
    mean = lambda d, cs: sum(d[c]["recall"] for c in cs if d[c]) / max(1, sum(1 for c in cs if d[c]))
    print("Criterion 1, coverage cases 12, 13, 15 at 80% recall or more:",
          all(t_all[c] and t_all[c]["recall"] >= 0.8 for c in cov), {c[:2]: f"{t_all[c]['recall']:.0%}" for c in cov if t_all[c]})
    drop = mean(b_all, core) - mean(t_all, core)
    print(f"Criterion 2, recall on 01 to 11 drops 5 points or less: {drop <= 0.05} (drop {drop:+.1%})")
    fb = sum(b_all[c]["false_positives"] for c in cases if b_all[c]); ft = sum(t_all[c]["false_positives"] for c in cases if t_all[c])
    print(f"Criterion 3, no more false positives: {ft <= fb} ({fb} -> {ft})")
    low = {c[:2]: f"{t_all[c]['main_path_residual']:.0%}" for c in cases if t_all[c] and t_all[c].get("main_path_residual") is not None and t_all[c]["main_path_residual"] < 0.8}
    print("Criterion 4, main path agreement 80% or more everywhere:", not low, low or "")
