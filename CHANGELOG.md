# Changelog

## 0.3.0 (unreleased)

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
