# PARA: Preemptive Agent Risk Assessment

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
```

## Quick start

```powershell
uv sync
uv run python scripts/validate.py examples/support_agent.assessment.json
uv run python scripts/render_report.py examples/support_agent.assessment.json --view both
```

Evals: save N skill outputs for a case under `evals/runs/<case_id>/`, then run:

```powershell
uv run python evals/run_consistency.py
```

Checks that run in CI on every push and pull request:

```powershell
uv run pytest -q
uv run python scripts/validate.py examples/support_agent.assessment.json --strict
uv run python evals/check_cases.py
```

## Status

The schema is 0.x and may change; see [CHANGELOG.md](CHANGELOG.md). Framework ids marked † in `references/crosswalk.md` still need to be checked against the pinned editions, and the SAFE-MCP rows need to be completed from the SAFE-MCP repository.

## Author

Jautau White

## License

Apache 2.0. Copyright 2026 Jautau White.
