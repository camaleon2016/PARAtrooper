# STRIDE for Agents

Run STRIDE per element across the design. Map each part of the design to a data flow diagram element:

| Design element | DFD element | Schema source |
|---|---|---|
| Agent | process | `subject` |
| MCP server or tool | process (external if third party) | `capabilities[].tool_ref`, `protocols` |
| Memory, vector store, RAG index | data store | `inputs` with source memory or retrieval; `capabilities` with write to a store |
| Protocol connection | data flow | `protocols[]` |
| Trust domain change | trust boundary | `subject.trust_domain`, `protocols[].peer_trust_level`, `inputs[].trust_level` |

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
