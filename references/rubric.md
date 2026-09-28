# PARA Rubric

Rubric version: 0.1.0. Applies to schema 0.2.x.

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

Credits are applied in this order. A finding cannot drop below `low`.

| Step | Control on the path | Credit |
|---|---|---|
| 1 | Structural, independent, preventive control that **severs** the path. The sink cannot be reached from the source under any model behavior. Examples: an egress allowlist that excludes attacker controlled destinations, or a credential scoped so the sensitive data cannot be read. | Residual = `low`. Stop. |
| 2 | Human approval gate on the sink (structural) | -2 tiers, floor `moderate` if the approver sees only a model generated summary, floor `low` if the approver sees the raw action (full destination and payload) |
| 3 | Structural containment that **narrows** without severing (rate limit, spend cap, partial credential scoping, sandbox with egress) | -1 tier total for this step, however many there are |
| 4 | Behavioral controls, and any control marked `dependent` | -1 tier total for this step, however many there are |
| 5 | Detective and corrective controls | No tier credit. Record them. They reduce `consequence` by at most one step when detection happens before harm completes. |

The credit caps in steps 3 and 4 are deliberate. Stacking five prompt instructions does not make an agent five times safer. Without the caps, teams could lower their rating by adding text.

The `partially_dependent` structural controls (for example, a tool allowlist that can be chained around) are credited at step 3.

**Worked example** (`examples/support_agent.assessment.json`): the untrusted email reaches CRM read and then email send. The sink is S3 (irreversible egress of confidential data). Inherent is `critical`. The only preventive control is a prompt rule (behavioral, dependent), so step 4 applies: -1 gives a residual of `high`. Outbound logging is detective, so it gets no tier credit.

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
