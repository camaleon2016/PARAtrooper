# PARA Rubric

Rubric version: 0.3.3. Applies to schema 0.6.x.

This rubric turns design facts into tiers. The same facts must always produce the same tier. When you have to use judgment, write it down in the finding's evidence or rationale. Do not let it affect the tier without saying so.

## 1. Units of analysis

- **Path**: an ordered chain from a **source** (an entry in `inputs`) to a **sink** (an entry in `capabilities`), possibly through intermediate capabilities. A path exists when the source's `reaches_capabilities` includes the sink, or includes a capability whose output feeds the sink (for example, read then send).
- **Finding**: one path, or one toxic combination, with its evidence. Tiers are computed per finding and then rolled up into `rating`.

## 2. Classifying sources and sinks

### Source class (from `inputs[].trust_level`)

| Class | trust_level | Notes |
|---|---|---|
| U | `untrusted`, `unknown` | Includes any content an outsider can author: email, web, tickets, files, third party tool output, third party agents. |
| I | `internal` | Authored inside the organization but not by the principal the agent acts for (for example, internal wiki or a peer agent's output). |
| T | `trusted` | The principal's own direct instruction through an authenticated channel. |

Downgrade rules, applied before scoring:
- Output from a tool or peer agent that itself ingests U content is U. Trust does not go up as content passes through an agent.
- `from_agent_id` pointing to a `third_party` or `unknown` trust domain is U.

### Sink class (from `capabilities[]`)

| Class | Condition (any one is enough) |
|---|---|
| S3 severe | `reversibility: irreversible`; or `is_egress: true` with `data_sensitivity` confidential or restricted; or `action` in `spend`, `credential_access`, `configure`, `delegate`; or `action: execute` with `credential_scope` broad, shared_service_account, or unknown |
| S2 significant | `write` or `delete` on internal or higher data; `is_egress: true` with internal data; `execute` with least_privilege scope |
| S1 limited | `read` of internal or higher data with no S2 or S3 egress reachable on the same path; `write` on public data |
| S0 negligible | `read` of public data |

When a path runs through several capabilities, the sink class is the class of the highest capability on the path. The data sensitivity is the highest sensitivity read earlier on the path. This is what makes read then send a toxic combination: the sensitivity of the read becomes the sensitivity of the send.

## 3. Autonomy levels

| Level | Meaning | Example | How it is scored |
|---|---|---|---|
| A0 suggest only | Agent has no execution path to tools; a human performs every action | Drafts a reply that a human copies and sends | Architectural. Inherent tier capped at `low`. |
| A1 approval each step | Every tool call blocks on a human approval | IDE agent that asks before every file write and shell command | Scored as an approval gate control (residual), not inherent |
| A2 approval on sensitive | Only designated capabilities block on approval | Support agent that sends freely to the ticket requester but needs approval for new recipients | Scored as approval gate controls on the gated capabilities |
| A3 act then report | Acts without blocking, then humans review | Triage agent that updates tickets and emails customers, with a daily digest | Inherent baseline |
| A4 fully autonomous | Acts without review, may run open ended | Background agent that runs multi day tasks and spawns sub agents | Inherent baseline plus the autonomy modifier |

Why A1 and A2 count as controls: their gates live in orchestration config and can be removed or loosened without changing the agent. Scoring them as controls means they show up in the forecast under `autonomy_increase` and `control_removal`. If `autonomy.level` claims A1 or A2 but no approval control covers a sensitive capability (`approval_gate_ref` is missing), raise an `instructions` or finding note saying the declared autonomy is not supported by the design. For that capability, score it as A3.

## 4. Inherent risk

Inherent risk is computed from sources, sinks, and autonomy with no controls. Approval gates are not counted.

### Base matrix

| Source \ Sink | S3 | S2 | S1 | S0 |
|---|---|---|---|---|
| U | critical | high | moderate | low |
| I | high | moderate | low | low |
| T | moderate | low | low | low |

The T to S3 cell is `moderate` rather than `low` because a trusted principal with an ambiguous goal can still direct an irreversible action by accident (`ambiguous_goal`, `unbounded_scope`).

### Autonomy modifier (+1 tier, cap `critical`, applied at most once)

Apply it when the sink is S2 or S3 and any one of these holds:
- `autonomy.level` is `A4_fully_autonomous`
- `autonomy.can_spawn_agents` is true
- `autonomy.can_modify_own_config` is true
- `autonomy.max_unattended_steps` is null or greater than 25, and `max_runtime_minutes` is null

### Caps

- A0: inherent capped at `low`.

## 5. Residual risk

Residual risk is inherent risk after crediting controls that `covers` a capability or input on the path and whose `status` is `declared` or `verified`. Controls with status `missing_recommended` get no credit.

Credits are applied in this order. A finding cannot drop below `low`. **Each control earns credit at exactly one step**, the first one it qualifies for. A structural control that is `dependent` earns step 4 credit only, never step 3 and step 4 together.

| Step | Control on the path | Credit |
|---|---|---|
| 1 | Structural, independent, preventive control that **severs** the path, recorded with `severs_path: true` and evidence. Set it only after answering yes to all three: is the control enforced outside the model; does it work regardless of model capability; and does it make the sink **unreachable** from the source, not merely harder to reach? Examples: an egress allowlist that excludes attacker controlled destinations, or a credential scoped so the sensitive data cannot be read. | Residual = `low`. Stop. |
| 2 | Human approval gate on the sink (structural), referenced by the capability's `approval_gate_ref` | Credit depends on `approval_volume`: `low` earns -2 tiers; `high` or `unknown` earns -1. The final residual cannot go below `moderate` unless the gate has `approval_review_mode: raw_action` **and** `approval_volume: low`. A gate with no review mode is scored as `model_summary`; with no volume, as `unknown`. |
| 3 | Structural preventive or containment controls that are `independent` or `partially_dependent`, **narrow** without severing, and **constrain the sink** of the path they cover (`constrains_sink: true`): a rate limit or spend cap on the sink, partial credential scoping, a recipient restriction. A sandbox that leaves the sink reachable (for example, unrestricted network egress) does not constrain it and earns nothing here. | -1 tier total for this step, however many there are |
| 4 | Behavioral controls, and any control marked `dependent` | -1 tier total for this step, however many there are |
| 5 | Detective and corrective controls | No tier credit. Record them. They reduce `consequence` by at most one step when detection happens before harm completes. |

The credit caps in steps 3 and 4 are deliberate. Stacking five prompt instructions does not make an agent five times safer. Without the caps, teams could lower their rating by adding text.

The `partially_dependent` structural controls (for example, a tool allowlist that can be chained around) are credited at step 3.

Approval volume (step 2): use `low` only when the design says each approver sees fewer than about 20 requests a day, or says each request is reviewed individually; `high` for more than that, or when approval is granted once and remembered; `unknown` when the artifacts do not say. The v0.3.x backtests showed why: the GitHub MCP incident's approval prompt failed under real approval volume, and both Claude and GPT-5.4 runs judged it weaker than the old two tier credit.

The approval gate floor applies to the final residual, after steps 3 and 4. Stacking other controls on top of a summary gate cannot push the residual below `moderate`, because the approver is still deciding on the model's description of the action.

**Residual equals the floor these credits produce.** Do not choose a different tier by judgment. If you believe a credited control deserves less credit than its classification gives it, fix the classification (mechanism, dependence, review mode, or what it covers) so the credit changes, rather than overriding the tier. When a design fact the classifications cannot express still makes the floor too low, you may rate residual higher, and you must state that fact in `residual_rationale`; from rubric 0.3.2 the validator rejects a residual above the floor without one. Never rate residual below the floor; the validator rejects it.

`scripts/validate.py` computes the floor from the controls on the path. It rejects a residual below the floor, and a residual above it without a `residual_rationale`.

The v0.3.1 eval batch showed why this rule exists: every run kept residual at or above the floor, but some runs raised it by unstated judgment, so runs of the same design disagreed. Stating the reason makes the disagreement reviewable.

**Worked example** (`examples/support_agent.assessment.json`): the untrusted email reaches CRM read and then email send. The sink is S3 (irreversible egress of confidential data). Inherent is `critical`. The only preventive control is a prompt rule (behavioral, dependent), so step 4 applies: -1 gives a residual of `high`. Outbound logging is detective, so it gets no tier credit.

## 5a. Property findings

Some risks have no attack path: a missing property such as attributable provenance, a spend or step limit, or a rate limit. Record them as findings with `finding_kind: property`, list the affected capabilities in `affected_refs`, and leave `attack_path` empty.

**Consequence.** A missing property only matters as much as the actions it leaves unchecked. Rate a property finding above `low` only when at least one affected capability is **consequential**: it writes, deletes, executes, configures, spends, delegates, accesses credentials, or sends data outside the trust boundary (`is_egress`). When every affected capability only reads and answers the authenticated requester, the missing property is hygiene, not exposure: rate it `low`. In the v0.4.0 batches, runs on a well controlled Q&A agent rated a missing audit trail `moderate`, which overstated the risk of an agent that changes nothing.

**Precedence.** When every source that could trigger the harm is trusted or internal, and the harm comes from a missing limit or a missing record, use a property finding, not a path finding from the internal source. A path finding from an internal source plus the autonomy modifier would rate it `critical`, which section 5a reserves for complete attack paths from untrusted sources.

1. **Sink class.** Take the highest sink class (section 2) among `affected_refs`.
2. **Base tier.** Use the **I row** of the base matrix: S3 `high`, S2 `moderate`, S1 and S0 `low`. A missing property is exposed to internal error and misuse as readily as to an attacker.
3. **Autonomy modifier.** Apply section 4's modifier.
4. **Cap.** A property finding alone never exceeds `high`. `critical` is reserved for complete attack paths. When a missing property makes a path finding worse (for example, no provenance on the exfiltration path), record it on the path finding instead.
5. **Residual.** Only a control that restores the missing property earns credit: one tier, and only if it is structural and not dependent, and recorded with `restores_property: true`. Tamper evident, attributable action records restore provenance; hard spend, rate, or step limits restore limits; pinned and verified definitions restore component integrity. Approval prompts, prompt instructions, allowlists, and ordinary logs restore none of these, so they earn nothing on a property finding. In the v0.4.x batches, runs on every model rated property findings above a floor that had credited such controls.

### Designs with no complete path today

When no untrusted source reaches a sensitive sink today, there is no present path finding above `low`. Risks that depend on planned changes are `horizon: forecast` findings. Do not promote them to present findings to make them visible; the forecast rating carries them.

## 5c. Supply chain findings

A finding tagged ASI04 (a compromised, substituted, or unverified tool, server, or peer agent) is about a component that controls what the agent sees. An approval prompt and a prompt instruction both work inside that context, so neither earns credit against it, whatever the review mode. Credit comes only from structural controls on the component itself, such as pinning, signature or identity verification, or an allowlist of exact definitions, at the step they qualify for. Runs on every model consistently rated these findings above floors that had credited approval prompts and prompt instructions.

## 6. Forecast risk

The forecast is a **conditional** claim, not a probability. It has this form:

> If trigger T occurs, controls C1..Cn stop constraining the path, and the finding's tier becomes X.

To compute it:
1. Pick the triggers that apply to this design (see `control_decay.md` for each trigger's watch signal and the control classes it defeats).
2. Remove every control that the trigger defeats:
   - `dependent` controls fail under `model_upgrade`, `longer_task_horizon`, and `autonomy_increase`.
   - `partially_dependent` controls fail under the triggers listed for their control type in `control_decay.md`.
   - Enumerated denylists fail under `new_tool`, `new_mcp_server`, `new_peer_agent`, and `data_scope_expansion`. Enumerated allowlists do not.
   - Human approval gates fail under `autonomy_increase` and `control_removal`. They degrade under volume, which is approval fatigue (see `control_decay.md`).
   - Any control fails under `control_removal` if its owner can disable it without review.
3. For additive triggers (`new_tool`, `new_mcp_server`, `new_peer_agent`, `data_scope_expansion`), also re-evaluate the sink class. Assume the addition is at the most common sensitivity for that deployment unless the design constrains it.
4. Recompute residual with the remaining controls. That result is `projected_risk`.

**Every finding has a `forecast` block,** present findings included. A forecast is PARA's core claim, so it is never optional. If no trigger would change a finding's tier, still record the triggers you considered, leave `failing_controls` empty, and set `projected_risk` equal to `residual_risk`. That is a real result: it says the design holds against those changes. The validator rejects any finding without a forecast.

Invariants:
- `projected_risk` ≥ `residual_risk`.
- `failing_controls` lists only controls that are present in `controls`.
- A finding with `horizon: forecast` has no complete path today. It must include a `forecast` block.

### Why this is falsifiable

Each forecast names specific controls and a specific trigger. That can be checked in two ways:
- **Backtesting**: rebuild the design from before a public incident, run PARA on it, and check whether the control that actually failed is in `failing_controls`.
- **Forward testing**: run a fixed injection suite against the current model and against a stronger model, with the same controls in place. If the bypass rate for dependent controls rises and the bypass rate for independent controls does not, the classification holds.

The accuracy claim PARA makes is about **which control fails first and why**. It does not claim when an incident will happen.

## 7. Rollup to `rating`

- `rating.inherent` = max `inherent_risk` over findings with `horizon: present`.
- `rating.residual` = max `residual_risk` over findings with `horizon: present`.
- `rating.forecast` = max of `rating.residual` and every `forecast.projected_risk` over all findings.
- No findings: `low` / `low` / `low`, and the rationale says which artifacts were reviewed.

`scripts/validate.py` enforces this rollup.

## 8. Likelihood and consequence (ISO/IEC 42001 6.1.2)

These are reported next to the tier. They do not replace it (see open decision 1).

| Likelihood | Guide |
|---|---|
| almost_certain | U source, no preventive control, sink reachable in one step |
| likely | U source, only behavioral preventive controls |
| possible | U source with structural containment, or I source with no preventive control |
| unlikely | Approval gate with raw action review, or structural control that nearly severs the path |
| rare | Path severed. Only misconfiguration or insider action reopens it. |

| Consequence | Guide |
|---|---|
| severe | Restricted data disclosed, irreversible financial or safety impact, or loss of control of credentials or config |
| major | Confidential data disclosed, or irreversible change to business records |
| moderate | Reversible change to internal data, or internal data disclosed |
| minor | Public data only, or effect fully reversible with no disclosure |

## 9. Confidence

- `high`: the path is evidenced by configuration or manifests (mcp.json, IaC, tool schema).
- `medium`: the path is inferred from documentation or the system prompt.
- `low`: the path is inferred because an artifact is missing. Also list the gap in `limitations`.

If the residual tier depends on a control that is only `declared`, say so in the finding's evidence. Verification would change the rating.
