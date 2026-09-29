# Control Decay

This file is what the forecast rests on. For every control, ask two questions: **where is it enforced** (mechanism), and **does it get weaker as the model gets more capable** (capability dependence)?

- **Structural** means it is enforced outside the model: in the runtime, network, identity layer, or orchestration.
- **Behavioral** means it only works if the model complies: instructions, self checks, or refusals.
- **Independent** means it works the same whether the model is weak or strong.
- **Partially dependent** means it is enforced outside the model, but a stronger model can route around it.
- **Dependent** means the model has to choose to obey it. A more capable model follows injected goals more competently, so these controls weaken.

## Control table

| Control | Mechanism | Dependence | How a more capable model defeats it | Fails under triggers |
|---|---|---|---|---|
| Prompt instruction forbidding an action | behavioral | dependent | Follows longer, more convincing injected goals. Reasons its way to exceptions ("the user clearly wants..."). Splits the forbidden action into steps that each look allowed. | model_upgrade, longer_task_horizon, autonomy_increase, intended_purpose_change |
| Model self check or reflection step | behavioral | dependent | The same model that was hijacked grades its own output. Better reasoning produces better rationalizations. | model_upgrade, longer_task_horizon |
| Spotlighting or delimiting untrusted content | behavioral | dependent | Only works if the model respects the delimiters. Adaptive attacks close the gap. | model_upgrade |
| Output filter or classifier (separate model) | behavioral | partially_dependent | Encoding, paraphrase, and steganography get past it. The filter does not scale with the actor, so the gap widens as the actor gets stronger. | model_upgrade, new_tool (new output channels) |
| Input injection classifier | behavioral | partially_dependent | The classifier sees content, not intent. Multi turn and multi document payloads get past it. | model_upgrade, new_mcp_server, data_scope_expansion |
| Tool allowlist (enumerated permitted tools) | structural | partially_dependent | Chains permitted tools into a forbidden effect, for example writing a file that a permitted tool later executes, or sending data through a ticket comment. | new_tool, new_mcp_server, model_upgrade |
| Tool or action denylist | structural | partially_dependent | New tools are allowed by default, so it fails open. It is also bypassed through equivalents. | new_tool, new_mcp_server, new_peer_agent, data_scope_expansion |
| Argument schema validation | structural | independent for type and range checks, partially_dependent for free text fields | Payloads are hidden in free text fields that validation cannot check semantically. | new_tool |
| Scoped credential (least privilege) | structural | independent | It does not decay. The model cannot use access it does not have. | control_removal, data_scope_expansion (the scope widens) |
| Network egress allowlist | structural | independent | It does not decay if destinations cannot be written by an attacker. It is partially dependent if an allowed destination is user writable (shared drives, issue trackers, pastebins, webhooks). | control_removal, new_tool (new egress channel) |
| Sandbox or isolated execution | structural | independent | It does not decay if escape paths are closed. Watch mounted secrets and network. | control_removal |
| Rate limit or spend cap | structural | independent | Does not decay, but only narrows the path. Low and slow attacks stay under it. | control_removal, longer_task_horizon |
| Human approval gate, raw action review | structural | independent | Does not decay with the model, but decays with volume through approval fatigue. | autonomy_increase, control_removal |
| Human approval gate, model summary review | structural | partially_dependent | The approver sees the model's description of the action. A more capable model writes more persuasive or selectively incomplete summaries (ASI09). | model_upgrade, autonomy_increase, control_removal |
| Recipient or destination confirmation bound to the record | structural | independent | Does not decay. The destination comes from the system of record, not from model output. | control_removal |
| Tool definition pinning or hashing | structural | independent | Does not decay. Counters rug pulls. | new_mcp_server (unpinned by default), control_removal |
| Logging and audit trail | structural | independent | It is detective. It does not prevent anything, and it only helps if someone reviews it. | control_removal |
| Anomaly detection on agent actions | structural | partially_dependent | A stronger model can stay within the learned baseline. | model_upgrade, longer_task_horizon |
| Memory write restrictions or provenance tags | structural | independent if enforced at the store; dependent if the model writes the tags | A stronger model learns to write believable provenance. | model_upgrade, data_scope_expansion |

## Approval fatigue (open decision 4)

A human approval gate is structurally independent of the model, but its effectiveness depends on **volume and framing**:
- **Volume**: approval rates tend to rise when a reviewer sees many requests per hour and nearly all are benign. Record the expected approvals per reviewer per day in the finding's evidence where known.
- **Framing**: if the approver sees a model generated summary rather than the raw action, the gate is `partially_dependent`. A more persuasive model lowers its effectiveness.

Scoring (schema 0.3.0 and later):
- Record `approval_review_mode` on every approval gate: `raw_action` or `model_summary`. A gate without it is scored as `model_summary`.
- Classify raw action gates as `independent`. Classify summary gates as `partially_dependent`.
- If the design implies high approval volume, list `autonomy_increase` and `longer_task_horizon` as triggers and name the gate in `failing_controls`. Put the volume assumption in `watch_signal`. Volume itself is not yet a schema field; it stays in evidence and `watch_signal`.
- A per call prompt that shows arguments only behind a collapsed link is `model_summary` in practice. Evals 10 and 11 are public incidents where this gate failed.

## Forecast triggers and watch signals

These double as the ISO/IEC 42001 8.2 significant change criteria. Any trigger that occurs means the assessment must be run again.

| Trigger | Defeats | Watch signal |
|---|---|---|
| model_upgrade | dependent controls; partially_dependent behavioral controls; summary approval gates | Model id or version string changes in config. `subject.model.swappable: true` means the change needs no review. |
| new_tool | denylists; tool allowlists (by chaining); output filters (new channel) | Tool manifest diff; new entries in the MCP tools/list response |
| new_mcp_server | denylists; unpinned definitions; input classifiers | MCP client config diff; new server entries |
| new_peer_agent | denylists; trust assumptions about peer output | New A2A agent card; new `accepts_tasks_from` entry |
| autonomy_increase | approval gates; all dependent controls | Approval gate removed or narrowed; `autonomy.level` raised; step limit raised |
| control_removal | any control its owner can disable without review | Config diff on guardrail settings; feature flag change |
| longer_task_horizon | dependent controls (instruction drift over long contexts); rate limits (low and slow) | Median steps per task or runtime per task rising |
| data_scope_expansion | scoped credentials (the scope widens); denylists; memory provenance | New data sources or wider credential grants |
| intended_purpose_change | instructions written for the original purpose | Product or prompt change that alters the agent's goal |

## Classification rules

1. When unsure between `dependent` and `partially_dependent`, choose `dependent` and set finding confidence to `medium`.
2. A structural control that is only as strong as a string the model writes is `partially_dependent`. Examples: a tag the model sets, or a destination the model chooses from a writable list.
3. A control is `independent` only if the path is still blocked when you assume the model fully cooperates with the attacker.
