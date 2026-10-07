# Toxic Combinations

A toxic combination is a set of elements that are each acceptable alone but risky together. Record the ordered chain in `attack_path`.

**`toxic_combination` holds element ids from the assessed document** (`input_id`, `capability_id`, `control_id`), for example `["in.inbound_email", "cap.crm_read", "cap.email_send"]`. It never holds pattern ids such as `TC1`; the validator rejects any id that is not defined in the document. Name the pattern in the finding title instead, for example "Lethal trifecta (TC1): ..."

## Core patterns

| Id | Pattern | Elements | Sink class | Notes |
|---|---|---|---|---|
| TC1 | Lethal trifecta | U source + read of confidential or restricted data + any egress | S3 | The most common exfiltration shape. Egress includes URLs, image rendering, ticket comments, commit messages, and webhook calls, not only "send" tools. |
| TC2 | Injected execution | U source + execute | S3 | Includes writing a file that something else later executes. |
| TC3 | Self modification | U source + `configure` on own config, prompt, tools, or memory | S3 | Persistence. Every later session inherits the compromise. |
| TC4 | Confused deputy | U or I source + capability with credential_scope broader than the principal's | S3 or S2 | The agent acts with authority the requester does not have. |
| TC5 | Memory laundering | U source + write to memory + later read of memory treated as I or T | Sink of the later read | Trust goes up over time. |
| TC6 | Spend loop | U source + spend + unbounded steps | S3 | Cost harvesting. Denial of wallet. |
| TC7 | Authority laundering | Approved task + delegation with `approval_context_propagates: false` + peer holding S3 | S3 | Approval is given for one thing and used for another. |
| TC8 | Split trifecta (phase two) | The three TC1 elements spread across different agents on one path | S3 | Each agent is clean alone. Detected by the composition engine. |
| TC9 | Summary gated irreversible action | Approval gate showing only a model summary + irreversible sink + U source | S3 | Decays under model_upgrade (ASI09). |

## Search procedure

1. For each input with trust class U, list its `reaches_capabilities`.
2. For each capability reached, follow data flow forward. Can its output feed another reached capability?
3. Stop at S3 sinks. Stop at S2 sinks if nothing reachable beyond them is S3.
4. Match each path against the table. When nothing matches, still file a finding if the rubric tier is moderate or higher.
5. Limit the path length to 6 steps. Longer paths go in `limitations`.
