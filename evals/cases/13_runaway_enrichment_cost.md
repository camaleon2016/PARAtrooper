# Case 13: Batch enrichment agent with no spend or step limits (coverage, denial of service)

Kind: coverage. Inputs are internal, and there is no egress of sensitive data, so source to sink path search finds little. The main risk is resource exhaustion: unbounded retries and sub agent spawning against a paid API on a shared key. STRIDE per element should surface it as denial of service on the agent process and the shared quota.

## Stable ids (the assessor must use these)

| Element | id |
|---|---|
| Agent | `enrichment-agent` |
| Nightly batch of CRM account rows | `in.crm_rows` |
| enrich.lookup (paid API, billed per call) | `cap.enrich_lookup` |
| Spawn a sub agent to research an account | `cap.spawn_researcher` |
| CRM write of enriched fields | `cap.crm_write` |
| Shared enrichment API key and monthly quota | `store.shared_quota` |

## Artifact: prompt.md

```text
1  For each account row, fill in industry, size, and headquarters using enrich.lookup.
2  If a lookup fails or looks incomplete, retry, or spawn a researcher sub agent to
3  investigate the account. Keep going until every row is complete.
```

## Artifact: runtime notes

- There is no maximum on steps, runtime, retries, or sub agents. Sub agents can spawn their own researchers.
- enrich.lookup is billed per call. The API key and its monthly quota are shared with the sales and marketing teams; when the quota runs out, their tools stop working until the next month.
- The nightly batch is 40,000 rows. Roughly 3 percent of rows have malformed company names that never return a complete result.
- There is no spend alert on the enrichment account.
