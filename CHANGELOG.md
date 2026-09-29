# Changelog

## 0.2.0 (2026-09-28)

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
