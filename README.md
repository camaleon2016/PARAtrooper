# PARA: Preemptive Agent Risk Assessment

[![CI](https://github.com/camaleon2016/PARAtrooper/actions/workflows/ci.yml/badge.svg)](https://github.com/camaleon2016/PARAtrooper/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/camaleon2016/PARAtrooper/badge)](https://scorecard.dev/viewer/?uri=github.com/camaleon2016/PARAtrooper)

PARA rates AI agent designs at design time on three horizons:

| Horizon | Question it answers |
|---|---|
| **Inherent** | How dangerous is this design with no controls? |
| **Residual** | How dangerous is it with the controls that exist today? |
| **Forecast** | Which of those controls fail first when the agent gets a stronger model, more tools, more peers, or more autonomy, and what does the risk become? |

The forecast works by classifying every control as **capability independent** (enforced outside the model) or **capability dependent** (relies on the model complying). Forecasts are conditional and falsifiable: *if trigger T, then controls C fail, and the tier becomes X.* PARA does not predict when an incident will happen. It predicts **which control breaks first and why**, and that claim can be backtested.

Phase one is an agent skill (`SKILL.md`). Phase two will be a standalone tool that composes many assessments into a topology. See [BUILD_OUTLINE.md](BUILD_OUTLINE.md).

## Framework alignment

OWASP Top 10 for Agentic Applications (2026), MITRE ATLAS, CSA MAESTRO, STRIDE with agentic classes, NIST AI RMF, ISO/IEC 42001, NIST SP 800-53, and SAFE-MCP. See [references/crosswalk.md](references/crosswalk.md) and [references/governance.md](references/governance.md).

## Layout

```
SKILL.md                 skill entry point and workflow
schema/                  versioned JSON contract (0.3.0)
references/              rubric, control decay, toxic combinations, crosswalk, STRIDE, governance, protocols
scripts/validate.py      schema + referential integrity + rubric invariants
scripts/render_report.py developer and reviewer Markdown views
examples/                worked assessment
evals/                   11 cases (vulnerable, clean, edge, forecast only,
                         assessor injection, and 2 public incident backtests),
                         expected results, consistency scoring, case checker
tests/                   pytest suite for the scripts and eval tooling
design/                  proposals for upcoming releases, with staged eval cases
```

## Quick start

Requires Python 3.10 or later. From the repository root (Windows PowerShell shown; use `python3` and `/` paths elsewhere):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\validate.py examples\support_agent.assessment.json
.\.venv\Scripts\python.exe scripts\render_report.py examples\support_agent.assessment.json --view both
```

Checks that run in CI on every push and pull request:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\validate.py examples\support_agent.assessment.json --strict
.\.venv\Scripts\python.exe evals\check_cases.py
```

## Evals

`evals/run_skill.py` runs the skill against every case through the Claude API. Evaluator notes (what a case tests, incident sources) are stripped before the model sees a case, so they cannot leak the expected answer. `evals/run_consistency.py` then scores recall, schema validity, false positives, and run to run agreement, and writes a publishable summary.

```powershell
$env:ANTHROPIC_API_KEY = "<your key>"
.\.venv\Scripts\python.exe evals\run_skill.py --model <model id> --runs 5
.\.venv\Scripts\python.exe evals\run_consistency.py --report evals\RESULTS.md
```

Run outputs in `evals/runs/` are committed with each published result so reviewers can audit them.

## Results

Results for the current release are in [evals/RESULTS.md](evals/RESULTS.md), including the two public incident backtests: would PARA, run before the incident, have named the attack path and the control that failed. [evals/RESULTS_NOTES.md](evals/RESULTS_NOTES.md) explains the numbers: how the batch was run, why some runs were not validator clean, and the known limitations they show.

## Status

The schema is 0.x and may change; see [CHANGELOG.md](CHANGELOG.md). MITRE ATLAS (2026.09) and SAFE-MCP ids are pinned and checked in CI. ISO/IEC 42001 clause and Annex A ids in `references/crosswalk.md` are checked against the licensed standard.

Security issues: see [SECURITY.md](SECURITY.md).

## Author

Jautau White

## License

Apache 2.0. Copyright 2026 Jautau White.
