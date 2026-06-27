# MCP Integration

Agent Council exposes an [MCP](https://modelcontextprotocol.io/) server so coding agents can start council reviews asynchronously.

## Start the MCP server

```bash
uv run quorum serve --mcp
```

This runs a stdio MCP server (not the HTTP web server). Configure it in your MCP client (Cursor, Claude Desktop, etc.) as a command-based server.

## Tools

### `quorum_review_start`

Start an async council review. Returns a `run_id` for polling.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | string | *required* | Code diff or question to review |
| `template` | string | `pr-review` | Template name |
| `mode` | string | `fast` | `fast` or `thorough` |
| `max_cost` | number | template default | Max USD spend |

### `quorum_review_poll`

Poll the status of a review run.

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | Run ID from `quorum_review_start` |

Returns status: `running`, `complete`, or `failed`.

### `quorum_review_get`

Retrieve the Decision Report for a completed run.

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | Run ID from `quorum_review_start` |

Returns the full Decision Report JSON including consensus, disagreements, risks, recommendation, and deliverable.

## Example workflow

```
1. Agent calls quorum_review_start with a PR diff
2. Agent polls quorum_review_poll until status is "complete"
3. Agent calls quorum_review_get and acts on the recommendation
```

Runs are persisted in SQLite alongside CLI and web runs — view them in the dashboard at `http://localhost:8000`.

## Requirements

- `OPENROUTER_API_KEY` must be set for live reviews
- The MCP server uses the same council engine as CLI and web (`quorum/council/engine.py`)
