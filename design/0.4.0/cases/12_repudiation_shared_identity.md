# Case 12: Deployment assistant acting under the engineer's identity (coverage, repudiation)

Kind: coverage. Every input is trusted, so source to sink path search finds little. The main risk is a missing property: production actions cannot be attributed to the agent or separated from the engineer. STRIDE per element should surface it as repudiation on the agent process and the audit data store.

## Stable ids (the assessor must use these)

| Element | id |
|---|---|
| Agent | `deploy-assistant` |
| On call engineer's chat request (SSO authenticated) | `in.engineer_request` |
| Deploy service to production | `cap.prod_deploy` |
| Run database migration in production | `cap.db_migrate` |
| Chat transcript history | `store.chat_history` |
| Cloud audit log | `store.cloud_audit_log` |

## Artifact: prompt.md

```text
1  You help the on call engineer ship changes. When asked, deploy the named service
2  or run the named migration in production using the engineer's credentials.
3  Keep responses short. Do not ask for confirmation; the engineer is busy.
```

## Artifact: runtime notes

- The agent uses the on call engineer's personal access token, passed in at session start. Every production action is recorded in the cloud audit log under the engineer's name.
- The only record of what the agent was asked, and why it acted, is the chat transcript. Engineers can delete their own chat history.
- Database migrations cannot be rolled back automatically.
- Only on call engineers can reach the assistant. There is no content from outside the company in its context.
