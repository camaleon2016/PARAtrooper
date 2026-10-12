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

Phase one is an agent skill in the open [Agent Skills](https://agentskills.io) format, so it runs on any platform that supports that standard, and as a single prompt file on platforms that don't. Phase two will be a standalone tool that composes many assessments into a topology. See [BUILD_OUTLINE.md](BUILD_OUTLINE.md).

## Framework alignment

OWASP Top 10 for Agentic Applications (2026), MITRE ATLAS, CSA MAESTRO, STRIDE with agentic classes, NIST AI RMF, ISO/IEC 42001, NIST SP 800-53, and SAFE-MCP. See [crosswalk.md](skills/para/references/crosswalk.md) and [governance.md](skills/para/references/governance.md).

## Use the skill

The skill is the folder `skills/para/`. Copy that folder, not the whole repository: the repository also holds evals and test runs that the skill does not need. Validation and reports need Python 3.10 or later; `jsonschema` is optional. On platforms that cannot run code, the skill validates with a plain language checklist instead and says so.

Once installed, ask your agent to assess an agent design: paste or point it at a system prompt, tool list, MCP configuration, or agent card, and ask something like "assess the risk of this agent."

### GitHub Copilot (VS Code agent mode, Copilot CLI, and the Copilot coding agent)

For one repository, copy the skill into `.github/skills/`:

```powershell
git clone https://github.com/camaleon2016/PARAtrooper.git $env:TEMP\PARAtrooper
New-Item -ItemType Directory -Force <your repo>\.github\skills | Out-Null
Copy-Item $env:TEMP\PARAtrooper\skills\para <your repo>\.github\skills\para -Recurse
```

For every repository you work in, copy it to your personal skills folder instead: `~/.copilot/skills/para` (on Windows, `$HOME\.copilot\skills\para`).

Verified in VS Code agent mode: Copilot discovered the skill, ran the validator, and produced valid assessments. See [evals/runs-copilot/NOTES.md](evals/runs-copilot/NOTES.md).

### Microsoft AI Foundry and Azure OpenAI

- **Foundry agents and other prompt based apps:** use `dist/para-prompt.md`, the whole skill in one file. Use it as the agent's instructions where the platform allows prompts that long (about 21,000 tokens), or upload it as a knowledge file and instruct the agent to follow it when asked to assess an agent design.
- **Your own app or pipeline:** send `dist/para-prompt.md` as the system prompt to any Azure OpenAI or Foundry model deployment through the v1 endpoint (`https://<resource>.openai.azure.com/openai/v1/`). `evals/run_skill.py --provider openai` is a working example.

### Gemini

- **Gemini CLI:** install `skills/para` in Gemini CLI's skills folder, following its Agent Skills documentation.
- **Gemini app or AI Studio:** use `dist/para-prompt.md` as the system instructions or as an uploaded file.

### ChatGPT and OpenAI Codex

- **Codex CLI:** copy `skills/para` to `~/.codex/skills/para`.
- **ChatGPT:** add `dist/para-prompt.md` to a project or custom GPT as a knowledge file, with an instruction to follow it for agent risk assessments. Custom instruction fields are too short for the whole skill.

### Claude

Copy `skills/para` to `.claude/skills/para` in a project, or to `~/.claude/skills/para` for all projects. In the Claude apps, upload it as a custom skill.

### What has been measured

Eval results are published for two model families: Claude (claude-sonnet-5) and OpenAI GPT-5.4 on Azure; see [Results](#results). A model that has not been evaluated may run the skill well or poorly, so check its output against the checklist the first few times.

## Layout

```
skills/para/             the skill (copy this folder to install)
  SKILL.md               entry point and workflow
  references/            rubric, control decay, toxic combinations, crosswalk, STRIDE,
                         governance, protocols, validation checklist
  schema/                versioned JSON contract (0.5.0)
  scripts/               validate.py and render_report.py
dist/para-prompt.md      the skill as one file, for platforms without Agent Skills support
tools/                   build_prompt_pack.py (regenerates dist/; CI checks it is current)
examples/                worked assessment
evals/                   13 cases, expected results, harness for Anthropic and OpenAI compatible
                         endpoints (including Azure), scoring, diagnostics, archived batches
tests/                   pytest suite
design/                  proposals for upcoming releases
```

## Developing

Requires Python 3.10 or later. From the repository root (Windows PowerShell shown; use `python3` and `/` paths elsewhere):

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe skills\para\scripts\validate.py examples\support_agent.assessment.json
.\.venv\Scripts\python.exe skills\para\scripts\render_report.py examples\support_agent.assessment.json --view both
```

Checks that run in CI on every push and pull request:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe skills\para\scripts\validate.py examples\support_agent.assessment.json --strict
.\.venv\Scripts\python.exe evals\check_cases.py
.\.venv\Scripts\python.exe tools\build_prompt_pack.py --check
```

After changing anything under `skills/para/`, run `tools\build_prompt_pack.py` to regenerate the prompt pack.

## Evals

`evals/run_skill.py` runs the skill against every case through a model API: Anthropic, or any OpenAI compatible endpoint, which covers OpenAI, Azure OpenAI and Azure AI Foundry, Gemini's compatibility endpoint, and local servers. Evaluator notes (what a case tests, incident sources) are stripped before the model sees a case, so they cannot leak the expected answer. `evals/run_consistency.py` then scores recall, validity, false positives, and run to run agreement, and writes a publishable summary.

To keep costs down: estimate first, run the five case smoke set once, and set a hard budget.

```powershell
# 1. Estimate (no calls). Prices are USD per million tokens from your provider's price list.
.\.venv\Scripts\python.exe evals\run_skill.py --set smoke --runs 1 --estimate --price-in <p> --price-cached-in <p> --price-out <p>

# 2. Smoke run on an Azure deployment, stopping at $5
$env:AZURE_OPENAI_API_KEY = "<key>"
.\.venv\Scripts\python.exe evals\run_skill.py --provider openai --api-key-env AZURE_OPENAI_API_KEY `
  --base-url https://<resource>.openai.azure.com/openai/v1/ --model <deployment> `
  --set smoke --runs 1 --out evals\runs-<deployment> --budget-usd 5 --price-in <p> --price-out <p>

# 3. Score that folder
.\.venv\Scripts\python.exe evals\run_consistency.py --runs-dir evals\runs-<deployment> --report evals\runs-<deployment>\RESULTS.md
```

Use one `--out` folder per model. Each run records token use and cost in a `run_NNN.meta.json` sidecar, and the folder's `manifest.json` records the model, provider, endpoint host (never the key), and every limit used. Run outputs are committed with each published result so reviewers can audit them.

## Results

### Across models

The same 13 cases, 5 runs each, with the same rubric and schema, on v0.3.5:

| Measure | Claude (claude-sonnet-5) | GPT-5.4 (Azure) |
|---|---|---|
| Mean recall | 95% | 93% |
| Validator clean | 100% | 98% |
| Runs with a false positive | 2 of 65 | 1 of 65 |
| GitHub MCP backtest (May 2025): recall, rated critical | 96%, every run | 100%, every run |
| Supabase MCP backtest (July 2025): recall, rated critical | 80%, every run | 92%, every run |
| Lowest main path residual agreement | 60% | 60% |
| Mean output tokens per assessment | 30,309 | 4,413 |
| Cost per assessment at list prices | about $0.31 | about $0.07 |

Details: [Claude v0.3.5](evals/runs-claude-v035/RESULTS.md) and [notes](evals/runs-claude-v035/RESULTS_NOTES.md); [GPT-5.4 v0.3.5](evals/runs-gpt-54-v035/RESULTS.md) and [notes](evals/runs-gpt-54-v035/RESULTS_NOTES.md). Earlier batches: [Claude v0.3.3](evals/RESULTS.md) and [GPT-5.4 v0.3.4](evals/runs-gpt-54/RESULTS.md).

### By version

The latest batch is in [evals/RESULTS.md](evals/RESULTS.md). Each released batch is archived with its run files and notes under `evals/archive/<version>/`:

- [v0.3.0 baseline](evals/archive/0.3.0/), including the two public incident backtests, with [notes](evals/archive/0.3.0/RESULTS_NOTES.md)
- [v0.3.1](evals/archive/0.3.1/), with [notes](evals/archive/0.3.1/RESULTS_NOTES.md) and the residual agreement diagnosis
- [v0.3.2](evals/archive/0.3.2/), measured but not released, with [notes](evals/archive/0.3.2/RESULTS_NOTES.md) on the forecast regression it revealed

## Status

The schema is 0.x and may change; see [CHANGELOG.md](CHANGELOG.md). MITRE ATLAS (2026.09) and SAFE-MCP ids are pinned and checked in CI. ISO/IEC 42001 clause and Annex A ids in `references/crosswalk.md` are checked against the licensed standard.

Security issues: see [SECURITY.md](SECURITY.md).

## Author

Jautau White

## License

Apache 2.0. Copyright 2026 Jautau White.
