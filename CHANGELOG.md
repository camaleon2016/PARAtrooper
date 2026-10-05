# Changelog

## 0.3.3 (2026-10-05)

Schema 0.5.0. Rubric 0.2.2. Includes every 0.3.2 change.

### Fixed
- Forecasts are required. Rubric section 6 and the validator now require a `forecast` block on every finding, present findings included. A forecast that changes nothing records the triggers considered with `projected_risk` equal to `residual_risk`. Without this rule, findings with a forecast dropped from 76 to 55 percent in the 0.3.2 batch, and the report did not show it.
- SKILL.md: the example of omitting empty fields used `forecast`, which caused that drop. It now uses `residual_rationale` and says never to omit `forecast`.

### Changed
- `design/0.4.0-stride-coverage.md`: adds a containment credit rule (section 14.4) and the 0.3.2 batch evidence for the approval volume factor (section 14.5). Baseline for v0.4.0 is now the 0.3.3 batch.

## 0.3.2 (not released)

Measured but not released: its batch showed findings with a forecast fell from 76 to 55 percent. See `evals/archive/0.3.2/RESULTS_NOTES.md`. Its changes ship in 0.3.3.

Schema 0.5.0. Rubric 0.2.1. Fixes found by the v0.3.1 batch and its residual diagnosis (see `evals/archive/0.3.1/RESULTS_NOTES.md`).

### Fixed
- Validator: an element may link to a protocol peer or the subject agent that shares its id. v0.3.1 rejected this, failing 2 runs.

### Changed
- Rubric 0.2.1, section 5: residual equals the floor the control credits produce. A higher residual requires `residual_rationale` naming the design fact the classifications cannot express. In v0.3.1, five runs raised residual above the floor without saying why, which lowered agreement.
- `control_decay.md`: every human approval gate must be wired through `approval_gate_ref`, and an approval granted once and then remembered is not a gate (no credit).
- SKILL.md:
  - record every control the artifacts mention, including weak ones
  - omit optional fields instead of writing `null`
  - escape quotes in evidence, and prefer paraphrase to long quotes

### Added
- Schema: `findings[].residual_rationale`.
- Validator warning when residual is above the floor without a rationale.
- Report: a main path residual agreement column, measured on the finding that contains each case's required attack path. The rollup takes the worst finding, so secondary findings can move it even when the main path is stable.
- `evals/compare_residuals.py`: shows which controls each run credited on the main path, and the rubric floor they allow.

## 0.3.1 (2026-10-03)

Schema 0.4.0. Rubric unchanged at 0.2.0. Fixes the schema and validator gaps found by the v0.3.0 baseline (see `evals/RESULTS_NOTES.md`).

### Added
- Schema: `elements` (data stores, peer agents, servers, and flows) so findings and controls can reference parts of a design that are not inputs or capabilities. Five baseline runs failed because they referenced data stores with no way to declare them.
- Schema: `planned` on capabilities, inputs, and elements, for roadmap items. Three baseline runs on the forecast only case invented ids for planned tools.
- Validator: present findings may not reference planned elements; forecast findings that do should name a trigger that adds them.
- SKILL.md rule 7 and step 3a: reference only ids defined in the document, keep artifact locators in evidence, and declare stores, peers, and planned items before referencing them.

### Fixed
- All scripts read JSON with `utf-8-sig`, so files saved with a byte order mark (PowerShell 5, some Windows editors) no longer crash the validator, scorer, or harness. Found while correcting the v0.3.0 manifest by hand.
- `run_consistency.py` terminal output says `validator_clean`, matching the report column.
- Validator: control `covers` now accepts the same references as attack paths (elements, peers, and the subject agent). Previously a control covering a peer agent failed while an attack path through the same peer passed.

### Changed
- `design/0.4.0-stride-coverage.md`: revised after the baseline. `elements` moved into v0.3.1; v0.4.0 now also proposes an approval volume factor, entry and impact tagging, and held out cases.

## 0.3.0 (2026-10-01)

### Added
- `evals/run_skill.py`: runs the skill against every case through the Claude API, saves each assessment, and records a manifest (model, commit, rubric and schema versions). Evaluator notes are stripped from cases before the model sees them. Unparseable output is saved and scored as a failed run.
- `run_consistency.py --report`: writes a publishable Markdown summary with a backtest section. Broken run files now score as invalid instead of crashing the scorer.
- Pinned framework id lists in `references/data/` (MITRE ATLAS 2026.09, SAFE-MCP catalog). `evals/check_cases.py` fails CI on any ATLAS or SAFE-MCP id that does not exist in the pinned edition.
- OpenSSF Scorecard workflow, pinned to commit SHAs.
- Harness: `run_skill.py` writes token usage and timing to `run_NNN.meta.json` sidecars; the report shows mean output tokens. `run_consistency.py` scores a new expected key, `required_stride_categories`, and accepts a `coverage` case kind.
- `design/0.4.0-stride-coverage.md`: proposed STRIDE per element coverage for v0.4.0, with two staged coverage cases (repudiation, denial of service) in `design/0.4.0/`.
- README badges for CI and Scorecard; Evals and Results sections; quick start without uv.

### Changed
- Crosswalk: MITRE ATLAS moved to 2026.09 and every id checked. All 85 SAFE-MCP techniques assigned to an ASI category. ASI07 now maps to AML.T0118 Autonomous AI Agent Communication; ASI09 to AML.T0067 and AML.T0130 and SAFE-T1403 Consent-Fatigue Exploit; NIST AI RMF ids for ASI09 corrected to MAP 3.5 and MEASURE 2.8.
- `evals/runs/` is now committed; only raw text from unparseable runs is ignored.
- Crosswalk ISO/IEC 42001: every Annex A id checked against the licensed text (A.6.2.6, A.7, A.8, A.10); A.6.2.4 AI system verification and validation added to ASI10. No unchecked ids remain in the crosswalk.

### Fixed
- Manifest records every `--max-tokens` value used and keeps the original start time when a batch is resumed (`last_resumed_at` added). The report column "Schema valid" is renamed "Validator clean", with a definition, because it counts rubric consistency errors as well as schema errors.
- `evals/tally_runs.py`: counts run outcomes (clean, truncated, unparseable, validator errors) and the most common validator error kinds.
- Pilot run findings: `run_skill.py` now reports truncation at `--max-tokens` clearly and defaults to 32,000 tokens, since the model's reasoning counts toward the limit. `--resume` redoes failed runs instead of skipping them. Run metadata the model cannot know (`assessed_at`, assessor version and model) is stamped by the harness.
- `toxic_combinations.md` and SKILL.md step 8 now state that `toxic_combination` holds element ids from the document, never pattern ids like `TC1`. The pilot run used pattern ids, which the validator rejects.
- Crosswalk 0.2.0 cited AML.T0104, which ATLAS 2026.08 renumbered to AML.T0115.002 (Publish Poisoned AI Artifacts: AI Agent Tools).
- Example assessment now pins ATLAS edition 2026.09.

## 0.2.0 (2026-09-29)

Schema 0.3.0. Rubric 0.2.0.

### Fixed
- `validate.py`: a structural control marked `dependent` was credited at both rubric step 3 and step 4. Each control now earns credit at exactly one step.
- `validate.py`: any structural, independent, preventive control was treated as severing the path. Step 1 now requires an explicit `severs_path: true` claim.
- `validate.py`: approval gates now apply the rubric step 2 floor. Residual cannot go below `moderate` unless the gate has `approval_review_mode: raw_action`.
- `render_report.py`: raw HTML in assessed artifacts passed through to the report, so a quoted `<img src=...>` could trigger an outbound fetch in viewers that render HTML. Angle brackets and ampersands are now entity encoded, and identifiers are rendered as safe code spans.
- `render_report.py`: forecast sentences now read "fails" for a single control.

### Added
- Schema: `controls[].approval_review_mode` (`raw_action` or `model_summary`) and `controls[].severs_path`.
- Validator: error when `severs_path` is set on a control that is not structural, independent, and preventive; warning when an approval gate has no `approval_review_mode`.
- Evals 04 to 11: third party MCP tool poisoning, A2A authority laundering, summary gated payment, memory poisoning, forecast only design, assessor injection, and backtests of the GitHub MCP (May 2025) and Supabase MCP (July 2025) incidents.
- `evals/check_cases.py`: checks that cases and expected files agree with each other and with the schema.
- `run_consistency.py`: scores `required_evidence_substrings` and `required_forecast_findings_min`, and applies `false_positive_threshold` to any case that sets it.
- Single CI workflow across Python 3.10 to 3.12 with actions pinned to commit SHAs, `persist-credentials: false`, and Dependabot for actions and pip.
- `.gitattributes` to normalize line endings to LF.

### Changed
- Crosswalk: pinned editions stated at the top; AML.T0086 checked; AML.T0104 added for ASI04; OWASP LLM column stays on the 2025 edition until checked against 2026.
- Removed duplicate copies of the schema and example from the repository root.

## 0.1.0

Initial skill, schema 0.2.0, rubric 0.1.0, three eval cases.
