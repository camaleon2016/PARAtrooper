# Changelog

## 0.4.5 (unreleased)

Rubric 0.3.3. Schema 0.6.2. Aligns two credit rules with what runs on every model kept concluding.

### Changed
- **Property findings (rubric section 5a):** only a control that restores the missing property earns credit, one tier, and only if it is structural, not dependent, and marked `restores_property: true`. Approval prompts, prompt instructions, allowlists, and ordinary logs earn nothing on a property finding. In the v0.4.4 GPT-5.4 batch, about half of the first attempt failures were property findings (no audit trail, no rate limit) rated above a floor that had credited an approval prompt or an allowlist.
- **Supply chain findings (new rubric section 5c):** on a finding tagged ASI04 (a compromised, substituted, or unverified tool, server, or peer agent), approval prompts and prompt instructions earn no credit, because both work inside the context that component controls. Structural controls on the component itself, such as pinning or identity verification, still count. About a third of the v0.4.4 first attempt failures were supply chain findings rated above such a floor.

### Added
- Schema 0.6.2: `controls.restores_property`. The validator warns when it is set on a behavioral or dependent control.

### Not changed
- Main path findings rated one tier above a floor credited by a prompt instruction against injection (for example, "ignore instructions in issues") remain a judgment the runs must explain in `residual_rationale`. That pattern is real but smaller, and changing it would move main path ratings across the suite; it needs its own test.

### Fixed before release
- The two new credit rules apply only to assessments made under rubric 0.3.3 or later. Rescoring older assessments with the first v0.4.5 build applied them retroactively and changed published validity figures; older assessments are again judged by the rubric they were made under.
- From rubric 0.3.3, a property finding whose inherent tier does not match section 5a is an error, not a warning, because the tier follows mechanically from the assessment's own capability declarations. In the first v0.4.5 GPT-5.4 batch, two runs rated a missing audit record on the read only HR policy agent `moderate` instead of `low`; once property findings stopped receiving credit from unrelated controls, those findings counted as false positives. SKILL.md now also says a reply to the authenticated requester is not egress.

## 0.4.4 (2026-10-28)

Measured on GPT-5.4 with one repair round: first attempt validity 48% (51% in v0.4.2), so the self check did not help; ratings, recall, and false positives held. See `evals/runs-gpt-54-v044/`.

Raises first attempt validity. Rubric (0.3.2) and schema (0.6.1) are unchanged; ratings are unaffected.

### Changed
- SKILL.md step 10 adds a final self check before validating: every finding rated above its floor must state the design fact in `residual_rationale`, secondary findings included, and no residual may sit below its floor. Since rubric 0.3.2 this has been the most common first attempt error on every model: the rating was a reasonable judgment, but its reason was left out. In the v0.4.2 batches it caused 10 of Claude's 12 single shot failures, and in a further GPT-5.4 batch 13 of 15 first attempts failed on it before one repair round fixed them.
- The validation checklist points to the same check.

### Fixed
- The eval harness now stamps `schema_version` on each run with the version the skill writes, as it already did for the rubric version. The validator switches rules on by the declared schema version, so a run that declared an older version would have skipped newer checks.

## 0.4.3 (2026-10-18)

Follows the SAFE-MCP project's rename to SAF-MCP. Schema 0.6.1. Rubric unchanged (0.3.2); rating behavior is unchanged, so the v0.4.2 results still describe the skill.

### Changed
- SAF-MCP replaces SAFE-MCP throughout the skill, crosswalk, and protocol checks. Technique ids keep the `SAFE-T` prefix, as upstream does.
- The pinned catalog is refreshed from `camaleon2016/SAF-MCP-skill` at commit 62e85d5 (2026-10-17): 86 techniques, 78 active and 8 deprecated. It is now `evals/data/saf_mcp_ids.tsv` and records each technique's lifecycle status.
- Crosswalk: five techniques take their new names (for example, SAFE-T1201 is now Post-Approval Tool Mutation, formerly MCP Rug Pull Attack). Deprecated techniques are marked and removed from the key column (ASI02 now lists SAFE-T1302 instead of SAFE-T1104; ASI06 lists SAFE-T3001 instead of SAFE-T1702). The new technique SAFE-T1112, Sampling Request Abuse, is assigned to ASI01.

### Added
- Schema 0.6.1: the `SAF_MCP` framework value. `SAFE_MCP` stays valid so earlier assessments keep validating; from schema 0.6.1 the validator warns when a new assessment uses it.

## 0.4.2 (2026-10-18)

Measured on three model families: Claude (single shot), GPT-5.4 and Gemini 3.1 Pro preview (one repair round each). Main path agreement was 100% in every case on Claude and Gemini; recall on cases 01 to 13 was 96%, 95%, and 91%. See `evals/runs-claude-v042/`, `evals/runs-gpt-54-v042/`, and `evals/runs-gemini-v042/`.

Rubric 0.3.2. Schema unchanged (0.6.0). Consistency fixes from the v0.4.x diagnosis.

### Changed
- `control_decay.md` rules 4 and 5, and SKILL.md step 7: a prompt instruction is always behavioral and never severs a path. It counts as a control only when it explicitly forbids or limits the action on the path; task descriptions are not controls, and an instruction that creates the risk (such as "treat recalled memories as the user's own instructions") is evidence of the weakness, never a control. In the v0.4.x batches, runs that credited task descriptions or the design's own risky instructions computed different residual floors for the same design: case 07 split between `low` and `high`, and case 16 between `high` and `critical`.
- Rubric 0.3.2: a residual above the floor without a `residual_rationale` is an error, as a residual below the floor already was. Unstated judgment above the floor split held out case 14 between `high` and `critical`. Assessments made under earlier rubric versions keep the warning.

### Added
- Validator warning when a control that looks like a prompt instruction is marked structural.

### Diagnosis behind this release
- The repair round did not cause the agreement drop in the v0.4.1 batch: most split runs were clean on the first attempt, and the runs it repaired moved toward the rubric floor.
- GPT-5.4's split on case 05 in v0.4.0 came from two runs rating residual below the floor with no controls credited; the validator rejected both, and one repair round corrects them.

### Fixed after the v0.4.2 batches
- Validator: property findings no longer receive step 4 credit from prompt instructions or other model dependent controls. Rubric section 5a already said such controls never restore a missing property, but the validator credited them, so a property finding rated at its true floor appeared to be above the floor. In the v0.4.2 Claude batch this produced 19 of 21 validator failures, and it inflated first attempt failures on GPT-5.4 and Gemini. All v0.4.2 runs are rescored with the corrected rule; repaired runs on GPT-5.4 and Gemini were repaired against the old rule, which the notes disclose.

## 0.4.1 (2026-10-14)

Measured on GPT-5.4 with one repair round: validator clean 79% on the first attempt and 100% after repair, at $0.118 per assessment. Case 09 rescored across versions with the corrected evidence check. See `evals/runs-gpt-54-v041-repair/`.

Measurement release. The skill, rubric (0.3.1), and schema (0.6.0) are unchanged.

### Added
- Eval harness repair pass (`--repair-rounds N`, default 0). After a run, the validator's own error messages are sent back to the model, which returns a corrected assessment, up to N times. This mirrors how the skill works on agent platforms, where it runs `scripts/validate.py` and fixes what it reports. The repair message carries only validator output, so it cannot leak expected answers, and it asks the model to change only what the errors require.
- The first attempt is kept as `run_NNN.single.json`, each run's sidecar records the errors before and after repair, and token use and cost cover every round.
- The report shows validator clean on the first attempt alongside validator clean after repair, and the manifest records `repair_rounds`.- Case 09's evidence check now accepts the ways runs cite the injected note ("pre-approval", or its address to security reviewers and automated assessors), not only the literal word "pre-approved". Every run on both models in v0.4.0 cited the note and tagged ASI01; the 75% recall was the wording check alone. The corrected expectation applies when scoring every version.


## 0.4.0 (2026-10-13)

Measured on Claude (3 runs per case) and GPT-5.4 (5 runs per case), with 3 held out cases: Claude passed all four success criteria and GPT-5.4 three; GPT-5.4's validator clean rate fell to 65%, mostly from incomplete STRIDE matrices. See `evals/runs-claude-v040/` and `evals/runs-gpt-54-v040/`.

Schema 0.6.0. Rubric 0.3.0. Implements `design/0.4.0-stride-coverage.md` and the additions the v0.3.x batches exposed on Claude and GPT-5.4. Rating behavior changes, so results are not directly comparable with 0.3.x without the held out cases.

### Added
- **STRIDE per element coverage.**
  - `stride_coverage` records one entry for every element and every STRIDE category that applies to its kind, with status `finding`, `mitigated`, `not_applicable` (with a reason), or `not_assessed` (with what is missing).
  - The validator requires complete coverage and checks every entry: findings must carry the category, mitigations must be real controls, and reasons need substance. It warns on behavioral mitigations for repudiation or denial of service, and on more than half the pairs marked not applicable.
  - The reviewer report shows a coverage matrix.
  - SKILL.md step 8b and `stride_agentic.md` define the minimum elements and applicability.
- **Property findings** (`finding_kind: property`, `affected_refs`) for risks with no attack path, such as no attributable provenance or no spend, rate, or step limit. Rubric section 5a tiers them from the internal row of the base matrix, with the autonomy modifier, capped at `high`.
- **Approval volume** (`controls[].approval_volume`). A low volume gate earns two tiers of credit; a high or unknown volume gate earns one. Only a raw action, low volume gate can bring residual below `moderate`.
- **Sink constraint** (`controls[].constrains_sink`). Rubric step 3 credits a structural control only when it actually limits the path's sink. A sandbox with open egress earns nothing.
- **Three held out eval cases** (14 to 16): a high volume raw action gate, a missing provenance risk, and calendar invite injection. They were written before 0.4.0 was built and never used to tune it.
- **Report:** a separate held out section and the not applicable rate.

### Changed
- `severs_path` is set only after answering three questions: enforced outside the model, independent of model capability, and making the sink unreachable rather than harder to reach. Misuse appeared in every 0.3.x batch.
- SKILL.md step 8: tag both the entry technique and the impact technique of an attack; and a design with no complete path today has no present path finding above `low`.
- The worked example declares elements and a complete STRIDE coverage matrix.

### Corrected after the first GPT-5.4 batch (unreleased)
The first v0.4.0 batch on GPT-5.4 was 29 percent validator clean. Most failures were the validator being stricter than the design intended, not the assessments being wrong. Those runs are kept in `evals/archive/0.4.0-pre/`.
- Coverage of pairs beyond the required set (an internal flow, repudiation on a log store) is allowed, as long as the element kind can carry the category. Rejecting it caused 34 failures.
- A coverage entry marked `finding` whose finding does not list the category is a warning, not an error, and the scorer counts the category either way. It caused 28 failures.
- An element may list its own id in `refs`. Cases whose stable ids are stores triggered 13 failures.
- STRIDE coverage is required only for schema 0.6.0 and later, so baseline runs of earlier versions are judged by their own rules.
- A residual below the floor the rubric credits allow is now an error, not a warning. A security assessment should never understate risk silently.
- Approval volume has a threshold: `low` means fewer than about 20 requests per approver a day, or each request reviewed individually.
- Precedence rule: when every triggering source is trusted or internal and the harm is a missing limit or record, use a property finding, not a path finding.
- The "below the floor" error applies from schema 0.6.0; earlier documents keep the warning they were built against.
- Scorer: `required_threat_ids_any` and `required_evidence_any` let a requirement accept alternatives where the skill's references allow more than one correct answer. Case 12's expectation now accepts ASI10 as well as ASI03 (the crosswalk maps repudiation to ASI10), and common phrasings of the engineer's token. The corrected expectation is applied when scoring every version, so comparisons stay fair.
- Rubric 0.3.1, section 5a: a property finding is rated above low only when an affected capability is consequential (it writes, deletes, executes, configures, spends, delegates, accesses credentials, or sends data outside the boundary). On the Claude batch, every run on the clean and forecast only designs rated a missing audit trail on a read only Q&A agent moderate, which counted as 6 false positives.
- SKILL.md and the crosswalk: an agent acting with a person's own credentials is tagged ASI03. Claude's case 12 runs tagged only ASI09 and ASI08.

## 0.3.5 (2026-10-12)

Measured on Claude and GPT-5.4: validator clean 100% and 98%, recall 95% and 93%; GPT-5.4's vocabulary failures fell from 5 to 0 and its recorded missing controls doubled. See `evals/runs-claude-v035/` and `evals/runs-gpt-54-v035/`.

Two model independent fixes exposed by the GPT-5.4 batch (see `evals/runs-gpt-54/RESULTS_NOTES.md`). Rubric unchanged (0.2.2). Schema structure unchanged (0.5.0); only field descriptions changed.

### Changed
- Schema descriptions now state the allowed values of `peer_trust_level` (a third party or external peer is `untrusted`, or `unknown`) and of `subject.trust_domain`, and which frameworks belong in `threat_refs` versus `governance_refs`. Four of GPT-5.4's five failures put `third_party` or `external` in `peer_trust_level`, and one put `NIST_AI_RMF` in `threat_refs`.
- SKILL.md step 10 names the three fields that are easy to confuse. Step 7 requires every structural recommendation to be recorded as a `missing_recommended` control covering the path.
- `control_decay.md` adds a Missing controls section, and `validation_checklist.md` adds the new warning.
- The example assessment records its two recommended controls as missing controls.

### Added
- Validator hints on schema errors: a wrong `peer_trust_level` value or a framework in the wrong list now says what to use instead, so a model that runs the validator can correct itself.
- Validator warning when a finding has structural recommendations but no `missing_recommended` control covering its attack path. In the GPT-5.4 batch, runs recorded far fewer missing controls than Claude while naming the same fixes in recommendations.
- The eval harness prints the API error message in each run's status line instead of only "api error".

## 0.3.4 (2026-10-10)

Portability release. Rubric, schema, and scoring are unchanged (rubric 0.2.2, schema 0.5.0), so the v0.3.3 Claude results still describe how the skill rates risk.

### Changed
- The skill now lives in `skills/para/`, which is all an installer needs to copy. The Agent Skills standard requires a skill's `name` to match its folder, and the repository root (`PARAtrooper`) did not.
- SKILL.md frontmatter adds `license`, `compatibility`, and `metadata` (author, version, repository), the optional fields the Agent Skills specification defines.
- The framework id lists used by CI moved from the skill's references to `evals/data/`.

### Added
- `references/validation_checklist.md`: every validator check in plain language, for platforms that cannot run code. SKILL.md points to it instead of asking the model to read Python.
- `validate.py` runs every rubric check even when `jsonschema` is not installed, and warns that the schema check was skipped.
- `dist/para-prompt.md`, built by `tools/build_prompt_pack.py`: the whole skill in one file for platforms without Agent Skills support, such as Azure AI Foundry agents, ChatGPT projects, and Gemini. CI fails if it is out of date.
- Eval harness:
  - `--provider openai` for any OpenAI compatible Chat Completions endpoint, including Azure OpenAI and Azure AI Foundry (v1 endpoint), OpenAI, Gemini's compatibility endpoint, and local servers. Options for the output limit parameter, reasoning effort, and JSON mode.
  - Cost controls: `--estimate` (tokens and dollars before any call), `--set smoke` (one case of each kind), `--budget-usd` (a hard stop based on reported usage), and per run cost in each `run_NNN.meta.json`.
  - `--out` on the harness and `--runs-dir` on the scoring scripts, so each model's runs live in their own folder.
  - The manifest records the provider and endpoint host. It never records keys.
- README: install instructions for GitHub Copilot, Azure, Gemini, ChatGPT and Codex, and Claude.
- Tests for the provider adapter, cost math, budget guard, prompt pack, the no `jsonschema` fallback, and Agent Skills frontmatter conformance.

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
