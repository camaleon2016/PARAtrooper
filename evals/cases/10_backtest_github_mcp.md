# Case 10: Backtest, GitHub MCP toxic agent flow (May 2025)

Kind: backtest. This is a reconstruction of the design before a publicly reported incident. The question is whether PARA, run before the incident, names the path and the control that actually failed.

Source: Invariant Labs, "GitHub MCP Exploited: Accessing private repositories via MCP," published May 26, 2025, https://invariantlabs.ai/blog/mcp-github-vulnerability. See also github/github-mcp-server issue 844 on the approval prompt.

What happened, summarized: an attacker opened an issue in the victim's public repository containing instructions for the agent. When the victim asked the agent to look at open issues, the agent read the issue, pulled private repository data with the same credential, and published it in a pull request on the public repository. The client asked for approval on tool calls, but the details sat behind a "See More" link next to a prominent "Continue" button.

## Stable ids (the assessor must use these)

| Element | id |
|---|---|
| Agent | `desktop-github-agent` |
| User request | `in.user_request` |
| Issues in the public repository | `in.public_issue` |
| get_file_contents on private repositories | `cap.read_private_repo` |
| create_pull_request on the public repository | `cap.create_pr_public` |
| Client tool call approval prompt | `ctl.tool_call_prompt` |

## Artifact: reconstructed configuration

```json
{
  "mcpServers": {
    "github": { "command": "docker", "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"] }
  }
}
```

## Artifact: reconstructed runtime notes

- The personal access token has repo scope across every repository the user owns, public and private.
- Anyone on GitHub can open issues in the public repository.
- The client asks for approval per tool call. Arguments are collapsed by default. Users approve many calls per session.
- The user's prompt: "Have a look at the open issues in my public repo."
