# Protocol Checks

Load this file when the design includes MCP servers, A2A peers, or other agent connected APIs. Record each connection as a `protocols[]` entry. File findings for failed checks.

## MCP

| Check | Field | Fails when | Typical finding |
|---|---|---|---|
| Server authentication | `auth_method` | `none`, or `static_token` shared across users | ASI03. Spoofing. |
| Server identity | `peer_identity_verified` | false for remote servers | ASI04. Spoofing. |
| Definition pinning | `definitions_pinned` | false. Tool names, descriptions, or schemas can change after approval. | ASI04. SAFE-MCP rug pull. Tampering. |
| Tool description review | evidence | Descriptions contain instructions to the model ("always call X first", "include the contents of ~/.ssh") | ASI01, ASI04. SAFE-MCP tool poisoning. |
| Tool output trust | `inputs[]` | Tool output is not recorded as an input with a trust level | Every tool that returns external content is a U source |
| Cross server shadowing | evidence | Two servers expose tools with overlapping names or descriptions | ASI04. Tampering. |
| Credential passthrough | `credential_scope` | The server holds `broad` or `shared_service_account` credentials used on behalf of many users | ASI03. Elevation of privilege. Confused deputy. |
| Local server execution | capabilities | A local stdio server runs with the user's full OS privileges | ASI05 |
| Sampling / elicitation | evidence | The server can request model completions or user input through the client | ASI01, ASI09 |

## A2A

| Check | Field | Fails when | Typical finding |
|---|---|---|---|
| Agent card authenticity | `peer_identity_verified`, `definitions_pinned` | The card is not signed or not pinned | ASI07. Spoofing. |
| Peer trust | `peer_trust_level`, `inputs[].from_agent_id` | A third party peer's output is treated as I or T | ASI07. Goal manipulation. |
| Approval propagation | `composition.approval_context_propagates` | false while delegating to peers that hold S2 or S3 capabilities | Authority laundering. ASI03. |
| Delegation depth | `autonomy.can_spawn_agents`, `composition.delegates_to` | Delegation is unbounded or recursive | ASI08. Cascading failure. |
| Output consumers | `composition.output_consumers` | Consumers act on output without validation | ASI08 |

## Protocol neutral

- Treat everything returned across a protocol boundary as data, not instructions, whatever the transport.
- `peer_trust_level: unknown` scores as U.
