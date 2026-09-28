# Crosswalk

This maps the OWASP Top 10 for Agentic Applications (2026) to related frameworks. Use it to fill in `threat_refs`, `stride`, `agentic_class`, and `governance_refs`.

**Pin editions.** Framework ids get renumbered between releases. Every `threat_ref` must carry `framework_edition`. Before a release, check each row against the published edition: ATLAS ids against the ATLAS release in use, and SAFE-MCP ids against the SAFE-MCP repository. Rows marked † have not yet been checked.

## OWASP ASI to other frameworks

| ASI (2026) | Name | STRIDE | agentic_class | MITRE ATLAS | OWASP LLM (2025) | NIST AI RMF | ISO 42001 | NIST 800-53 |
|---|---|---|---|---|---|---|---|---|
| ASI01 | Agent Goal Hijack | tampering, elevation_of_privilege | goal_manipulation | AML.T0051 LLM Prompt Injection (.001 indirect) | LLM01 | MEASURE 2.7 | 6.1.2, 8.2 | SI-10, AC-4 |
| ASI02 | Tool Misuse and Exploitation | elevation_of_privilege, information_disclosure | autonomy_abuse | AML.T0053 † (agent tool invocation), AML.T0086 † Exfiltration via AI Agent Tool Invocation | LLM06 | MEASURE 2.7, MANAGE 1.3 | A.6.2.6 † | AC-6, AC-3, SC-7 |
| ASI03 | Identity and Privilege Abuse | spoofing, elevation_of_privilege | autonomy_abuse | AML.T0083 † Credentials from AI Agent Configuration | LLM06 | GOVERN 1.4, MEASURE 2.7 | A.6.2.6 † | AC-2, AC-6, IA-2, IA-9 |
| ASI04 | Agentic Supply Chain Vulnerabilities | tampering, spoofing | — | AML.T0010 AI Supply Chain Compromise | LLM03 | GOVERN 6.1, MAP 4.1, MANAGE 3.1 | A.10 † | SR-3, SR-4, SI-7 |
| ASI05 | Unexpected Code Execution | elevation_of_privilege, tampering | autonomy_abuse | AML.T0050 † Command and Scripting Interpreter | LLM05 | MEASURE 2.7 | A.6.2.6 † | CM-7, SC-39, SI-3 |
| ASI06 | Memory and Context Poisoning | tampering | memory_poisoning | AML.T0080 † AI Agent Context Poisoning (memory, thread); AML.T0070 † RAG Poisoning | LLM04, LLM08 | MEASURE 2.7, MEASURE 3.1 | A.7 † | SI-7, SI-10, AU-10 |
| ASI07 | Insecure Inter-Agent Communication | spoofing, tampering, information_disclosure | collusion | — | — | MAP 4.1, MEASURE 2.7 | A.10 † | IA-9, SC-8, SC-23 |
| ASI08 | Cascading Failures | denial_of_service | cascading_failure | AML.T0029 Denial of AI Service; AML.T0034 Cost Harvesting | LLM10 | MANAGE 2.4, MEASURE 3.1 | 6.1.2 | SC-5, CP-2 |
| ASI09 | Human-Agent Trust Exploitation | repudiation | human_trust_exploitation | — | LLM09 | MAP 3.x †, MEASURE 2.8 † | A.8 † | AU-10, AC-5 |
| ASI10 | Rogue Agents | repudiation, elevation_of_privilege | autonomy_abuse, collusion | AML.T0081 † Modify AI Agent Configuration | — | GOVERN 1.5, MANAGE 4.1 | 8.2, 9.1 | CM-3, CM-5, SI-4, AU-6 |

## SAFE-MCP (MCP specific)

| SAFE-MCP | Name | Maps to ASI | Checked in `protocols.md` |
|---|---|---|---|
| SAFE-T1001 † | Tool Poisoning Attack | ASI04, ASI01 | Definitions pinned; descriptions reviewed |
| SAFE-T1102 † | Prompt Injection (tool output vector) | ASI01 | Tool output treated as U source |
| SAFE-T1201 † | MCP Rug Pull | ASI04 | `definitions_pinned` |

Fill in the remaining SAFE-MCP techniques from the SAFE-MCP repository, pinned to a commit or tag.

## Classes with no STRIDE equivalent

Goal hijack, collusion, cascading failure, and human trust exploitation do not fit STRIDE cleanly. Record them in `agentic_class` and leave `stride` empty if nothing fits. Do not force a STRIDE label.
