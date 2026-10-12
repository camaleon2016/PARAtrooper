# STRIDE for Agents

Run STRIDE per element across the design. Map each part of the design to a data flow diagram element:

| Design element | DFD element | Schema source |
|---|---|---|
| Agent | process | `subject` |
| MCP server or tool | process (external if third party) | `capabilities[].tool_ref`, `protocols` |
| Memory, vector store, RAG index | data store | `inputs` with source memory or retrieval; `capabilities` with write to a store |
| Protocol connection | data flow | `protocols[]` |
| Trust domain change | trust boundary | `subject.trust_domain`, `protocols[].peer_trust_level`, `inputs[].trust_level` |

## Recording coverage (`stride_coverage`)

From schema 0.6.0, every assessment records STRIDE per element in `stride_coverage`, and the validator rejects an assessment without it.

**Minimum elements.** Declare in `elements`:
- the subject agent, as a `process` (its `element_id` can be the subject `agent_id`);
- every input, as a `data_flow` (set `crosses_boundary` when its source is outside the trust domain), and the outside source as an `external_entity`;
- every egress capability, as a `data_flow` that crosses the boundary;
- every memory, vector store, log, audit record, quota, or configuration the design depends on, as a `data_store` (set `is_audit_record` on stores whose integrity makes actions attributable);
- every protocol peer, as a `process` (inside the trust domain) or an `external_entity`.

**Which categories apply.** The validator requires exactly these pairs:

| Element kind | Categories |
|---|---|
| process | spoofing, tampering, repudiation, information_disclosure, denial_of_service, elevation_of_privilege |
| external_entity | spoofing, repudiation |
| data_store | tampering, information_disclosure, denial_of_service, and repudiation when `is_audit_record` |
| data_flow | tampering, information_disclosure, denial_of_service, only when `crosses_boundary` is true |

**One entry per pair, with one status:**
- `finding`: the pair produces or confirms a finding. Name it in `finding_ids`, and add the category to that finding's `stride`.
- `mitigated`: a declared or verified control addresses it. Name it in `control_ids`. Prompt instructions cannot mitigate repudiation or denial of service.
- `not_applicable`: the category cannot apply to this element in this design. Give a specific reason tied to a design fact (at least 30 characters).
- `not_assessed`: the artifacts do not say enough. Say what is missing. This is an honest gap, not a failure.

**Missing properties are findings.** No attributable record of actions (repudiation) and no spend, rate, or step limit (denial of service) are findings with `finding_kind: property` (rubric section 5a), not `not_applicable`. If more than half the pairs end up `not_applicable`, look again; the validator warns at that point.

## Per element checklist

### Processes (agents, MCP servers)

- **Spoofing**: Is the peer identity verified (`peer_identity_verified`)? Is the auth method `none` or `static_token`? Can an agent card or server name be impersonated?
- **Tampering**: Can tool definitions change after approval (`definitions_pinned: false`)? Can the agent change its own config (`can_modify_own_config`)?
- **Repudiation**: Are agent actions logged under a human identity? Is there action provenance that separates agent from user?
- **Information disclosure**: Can any tool invocation carry data outside the boundary (`is_egress`)? Include side channels such as URLs, image fetches, and ticket comments.
- **Denial of service**: Are runaway loops possible? Check `max_unattended_steps` null, spend with no cap, and recursive delegation.
- **Elevation of privilege**: Does the agent hold broader credentials than the principal (a confused deputy)? Can delegation reach capabilities the principal lacks?

### Data stores (memory, RAG)

- **Tampering**: Can U sources write to memory that is later read as I or T? That is memory poisoning (`agentic_class: memory_poisoning`).
- **Information disclosure**: Can retrieval return one tenant's data to another?
- **Repudiation**: Do memory writes carry provenance that the model cannot forge?

### Data flows (protocol edges)

- **Spoofing**: Is there mutual authentication (`mtls`, `signed_identity`)?
- **Tampering**: Is there integrity protection in transit and on definitions?
- **Information disclosure**: Is the flow encrypted? Is it logged with payloads that include secrets?

### Trust boundaries

- Every place where `trust_level` changes across a flow is a boundary. **Content must never gain trust by crossing a boundary.** If a U input passes through an agent and comes out labeled I or T, file a finding with `agentic_class: goal_manipulation`. In phase two this is called injection propagation.

## Agentic classes (not covered by STRIDE)

| agentic_class | Look for |
|---|---|
| goal_manipulation | A U source that can reach decision making. Indirect injection. |
| autonomy_abuse | Capability used beyond intent. Unbounded steps. Self spawning. |
| memory_poisoning | U content persisted and later treated as trusted |
| cascading_failure | One agent's bad output consumed by `output_consumers` without validation |
| collusion | Two or more agents that together get around a control that binds each one alone |
| human_trust_exploitation | Approvers or users relying on model generated summaries or claims |
