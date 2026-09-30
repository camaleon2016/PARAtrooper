# Crosswalk

This maps the OWASP Top 10 for Agentic Applications (2026) to related frameworks. Use it to fill in `threat_refs`, `stride`, `agentic_class`, and `governance_refs`.

## Pinned editions

Framework ids get renumbered between releases, so every `threat_ref` carries `framework_edition`. This table was checked against:

| Framework | Edition | Source checked |
|---|---|---|
| OWASP Agentic Top 10 | `2026` | Published list, December 2025 |
| MITRE ATLAS | `2026.09` | `mitre-atlas/atlas-data`, `dist/ATLAS-latest.yaml`, content version 2026.09 |
| SAFE-MCP | `SAFE-MCP-skill@e54523b` | `camaleon2016/SAFE-MCP-skill`, `src/data/techniques.json`, commit e54523b9569e (2026-09-18); upstream is `safe-agentic-framework/safe-mcp` |
| NIST AI RMF | `1.0` | AI RMF core subcategory text |
| OWASP LLM Top 10 | `2025` | Kept on 2025; see note below |
| ISO/IEC 42001 | `2023` | Clause numbers and every Annex A id (A.6.2.4, A.6.2.6, A.7, A.8, A.10) checked against the licensed text |

Renumbering example: ATLAS 2026.08 folded "Publish Poisoned AI Agent Tool" (formerly AML.T0104) into AML.T0115.002. PARA 0.2.0 cited the old id. Assessments must use the edition they cite.

OWASP LLM note: the 2026 edition was published August 4, 2026. The LLM column stays on 2025 until each id is checked against the 2026 list, so set `framework_edition: "2025"` on those refs.

## OWASP ASI to other frameworks

| ASI (2026) | Name | STRIDE | agentic_class | MITRE ATLAS (2026.09) | Key SAFE-MCP | OWASP LLM (2025) | NIST AI RMF | ISO 42001 | NIST 800-53 |
|---|---|---|---|---|---|---|---|---|---|
| ASI01 | Agent Goal Hijack | tampering, elevation_of_privilege | goal_manipulation | AML.T0051 LLM Prompt Injection (.001 Indirect) | SAFE-T1102, SAFE-T1401, SAFE-T1402 | LLM01 | MEASURE 2.7 | 6.1.2, 8.2 | SI-10, AC-4 |
| ASI02 | Tool Misuse and Exploitation | elevation_of_privilege, information_disclosure | autonomy_abuse | AML.T0053 AI Agent Tool Invocation; AML.T0086 Exfiltration via AI Agent Tool Invocation; AML.T0101 Data Destruction via AI Agent Tool Invocation | SAFE-T1104, SAFE-T1703, SAFE-T1911, SAFE-T1914 | LLM06 | MEASURE 2.7, MANAGE 1.3 | A.6.2.6 | AC-6, AC-3, SC-7 |
| ASI03 | Identity and Privilege Abuse | spoofing, elevation_of_privilege | autonomy_abuse | AML.T0083 Credentials from AI Agent Configuration; AML.T0098 AI Agent Tool Credential Harvesting | SAFE-T1307, SAFE-T1308, SAFE-T1304 | LLM06 | GOVERN 1.4, MEASURE 2.7 | A.6.2.6 | AC-2, AC-6, IA-2, IA-9 |
| ASI04 | Agentic Supply Chain Vulnerabilities | tampering, spoofing | none | AML.T0010.005 AI Supply Chain Compromise: AI Agent Tool; AML.T0110 AI Agent Tool Poisoning; AML.T0115.002 Publish Poisoned AI Artifacts: AI Agent Tools | SAFE-T1001, SAFE-T1201, SAFE-T1008, SAFE-T1003 | LLM03 | GOVERN 6.1, MAP 4.1, MANAGE 3.1 | A.10 | SR-3, SR-4, SI-7 |
| ASI05 | Unexpected Code Execution | elevation_of_privilege, tampering | autonomy_abuse | AML.T0050 Command and Scripting Interpreter | SAFE-T1101, SAFE-T1111, SAFE-T1303 | LLM05 | MEASURE 2.7 | A.6.2.6 | CM-7, SC-39, SI-3 |
| ASI06 | Memory and Context Poisoning | tampering | memory_poisoning | AML.T0080 AI Agent Context Poisoning (.000 Memory, .001 Thread); AML.T0070 RAG Poisoning; AML.T0099 AI Agent Tool Data Poisoning | SAFE-T1204, SAFE-T1702, SAFE-T2106 | LLM04, LLM08 | MEASURE 2.7, MEASURE 3.1 | A.7 | SI-7, SI-10, AU-10 |
| ASI07 | Insecure Inter-Agent Communication | spoofing, tampering, information_disclosure | collusion | AML.T0118 Autonomous AI Agent Communication (.001 Direct Agent Communication); AML.T0073 Impersonation | SAFE-T1705 | none | MAP 4.1, MEASURE 2.7 | A.10 | IA-9, SC-8, SC-23 |
| ASI08 | Cascading Failures | denial_of_service | cascading_failure | AML.T0029 Denial of AI Service; AML.T0034.002 Cost Harvesting: Agentic Resource Consumption | SAFE-T1106, SAFE-T2102 | LLM10 | MANAGE 2.4, MEASURE 3.1 | 6.1.2 | SC-5, CP-2 |
| ASI09 | Human-Agent Trust Exploitation | repudiation | human_trust_exploitation | AML.T0067 LLM Trusted Output Components Manipulation; AML.T0130 AI Agent Response Biasing | SAFE-T1403 | LLM09 | MAP 3.5, MEASURE 2.8 | A.8 | AU-10, AC-5 |
| ASI10 | Rogue Agents | repudiation, elevation_of_privilege | autonomy_abuse, collusion | AML.T0081 Modify AI Agent Configuration; AML.T0103 Deploy AI Agent | SAFE-T1901, SAFE-T1903 | none | GOVERN 1.5, MANAGE 4.1 | 8.2, 9.1, A.6.2.4, A.6.2.6 | CM-3, CM-5, SI-4, AU-6 |

For ASI10, A.6.2.4 supplies the documented baseline of intended behavior that makes an agent "rogue" when it departs from it, and its verification criteria should be rerun whenever a forecast trigger fires (clause 8.2). Detecting departure at runtime belongs to operation and monitoring (A.6.2.6).

SAFE-T1403 Consent-Fatigue Exploit is the technique behind the approval fatigue scoring in `control_decay.md` and the backtests in evals 10 and 11.

## SAFE-MCP techniques by ASI category

Every technique in the pinned SAFE-MCP catalog (85) is assigned to exactly one primary ASI category. Assignments are PARA's, derived from each technique's tactic and description; many techniques also touch a second category. Four discovery techniques are preconditions rather than risks in their own right and map to no ASI category.

| ASI | SAFE-MCP techniques |
|---|---|
| ASI01 Agent Goal Hijack | SAFE-T1102 Prompt Injection (Multiple Vectors); SAFE-T1110 Multimodal Prompt Injection via Images/Audio; SAFE-T1309 Privileged Tool Invocation via Prompt Manipulation; SAFE-T1401 Line Jumping; SAFE-T1402 Instruction Steganography; SAFE-T1603 System Prompt Disclosure |
| ASI02 Tool Misuse | SAFE-T1103 Fake Tool Invocation (Function Spoofing); SAFE-T1104 Over-Privileged Tool Abuse; SAFE-T1105 Path Traversal via File Tool; SAFE-T1302 High-Privilege Tool Abuse; SAFE-T1606 Directory Listing via File Tool; SAFE-T1701 Cross-Tool Contamination; SAFE-T1703 Tool-Chaining Pivot; SAFE-T1801 Automated Data Harvesting; SAFE-T1802 File Collection; SAFE-T1803 Database Dump; SAFE-T1804 API Data Harvest; SAFE-T1805 Context Snapshot Capture; SAFE-T1910 Covert Channel Exfiltration; SAFE-T1911 Parameter Exfiltration; SAFE-T1912 Stego Response Exfil; SAFE-T1913 HTTP POST Exfil; SAFE-T1914 Tool-to-Tool Exfil; SAFE-T1915 Cross-Chain Laundering via Bridges/DEXs; SAFE-T2101 Data Destruction; SAFE-T2104 Fraudulent Transactions |
| ASI03 Identity and Privilege Abuse | SAFE-T1005 Exposed Endpoint Exploit; SAFE-T1007 OAuth Authorization Phishing; SAFE-T1009 Authorization Server Mix-up; SAFE-T1202 OAuth Token Persistence; SAFE-T1206 Credential Implant in Config; SAFE-T1304 Credential Relay Chain; SAFE-T1306 Rogue Authorization Server; SAFE-T1307 Confused Deputy Attack; SAFE-T1308 Token Scope Substitution; SAFE-T1408 OAuth Protocol Downgrade; SAFE-T1502 File-Based Credential Harvest; SAFE-T1503 Env-Var Scraping; SAFE-T1504 Token Theft via API Response; SAFE-T1505 In-Memory Secret Extraction; SAFE-T1506 Infrastructure Token Theft; SAFE-T1507 Authorization Code Interception; SAFE-T1706 OAuth Token Pivot Replay; SAFE-T1707 CSRF Token Relay |
| ASI04 Agentic Supply Chain | SAFE-T1001 Tool Poisoning Attack (TPA); SAFE-T1002 Supply Chain Compromise; SAFE-T1003 Malicious MCP-Server Distribution; SAFE-T1004 Server Impersonation / Name-Collision; SAFE-T1006 User-Social-Engineering Install; SAFE-T1008 Tool Shadowing Attack; SAFE-T1201 MCP Rug Pull Attack; SAFE-T1203 Backdoored Server Binary; SAFE-T1205 Persistent Tool Redefinition; SAFE-T1207 Hijack Update Mechanism; SAFE-T1301 Cross-Server Tool Shadowing; SAFE-T1405 Tool Obfuscation/Renaming; SAFE-T1406 Metadata Manipulation; SAFE-T1407 Server Proxy Masquerade; SAFE-T1501 Full-Schema Poisoning (FSP); SAFE-T1704 Compromised-Server Pivot; SAFE-T2107 AI Model Poisoning via MCP Tool Training Data Contamination |
| ASI05 Unexpected Code Execution | SAFE-T1101 Command Injection; SAFE-T1109 Debugging Tool Exploitation; SAFE-T1111 AI Agent CLI Weaponization; SAFE-T1303 Sandbox Escape via Server Exec; SAFE-T1305 Host OS Priv-Esc (RCE); SAFE-T2103 Code Sabotage |
| ASI06 Memory and Context Poisoning | SAFE-T1204 Context Memory Implant; SAFE-T1404 Response Tampering; SAFE-T1702 Shared-Memory Poisoning; SAFE-T2106 Context Memory Poisoning via Vector Store Contamination; SAFE-T3001 RAG Backdoor Attack |
| ASI07 Insecure Inter-Agent Communication | SAFE-T1705 Cross-Agent Instruction Injection |
| ASI08 Cascading Failures | SAFE-T1106 Autonomous Loop Exploit; SAFE-T2102 Service Disruption |
| ASI09 Human-Agent Trust Exploitation | SAFE-T1403 Consent-Fatigue Exploit; SAFE-T2105 Disinformation Output |
| ASI10 Rogue Agents | SAFE-T1901 Outbound Webhook C2; SAFE-T1902 Covert Channel in Responses; SAFE-T1903 Malicious Server Control Channel; SAFE-T1904 Chat-Based Backchannel |
| Discovery (no ASI) | SAFE-T1601 MCP Server Enumeration; SAFE-T1602 Tool Enumeration; SAFE-T1604 Server Version Enumeration; SAFE-T1605 Capability Mapping |

## Classes with no STRIDE equivalent

Goal hijack, collusion, cascading failure, and human trust exploitation do not fit STRIDE cleanly. Record them in `agentic_class` and leave `stride` empty if nothing fits. Do not force a STRIDE label.

## Updating this file

1. Regenerate `references/data/atlas_ids_<edition>.tsv` from the new ATLAS release and update the file name in `evals/check_cases.py`. CI then rejects any `AML.` id that does not exist in the pinned edition.
2. Regenerate `references/data/safe_mcp_ids.tsv` when the SAFE-MCP catalog changes, update the pin above, and assign any new technique to one ASI row.
3. Bump the edition strings above and note renumbered ids in the CHANGELOG.
