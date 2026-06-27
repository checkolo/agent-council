# Agent Council

**Multi-role deliberation with replayable Decision Reports — where models disagree, with evidence.**

Agent Council runs a panel of role-conditioned LLM specialists, surfaces where they disagree, and synthesizes a structured **Decision Report** you can replay, share, and audit. Built by **Planner Pannel**.

The CLI and Python package are named `quorum`; this repository is **Agent Council**.

---

## Why Agent Council?

Single-model reviews miss perspective. Agent Council convenes a **council** — Architect, Security, Performance, QA, or custom roles — each with a distinct lens. A **judge** synthesizes their outputs into one report: consensus, disagreements, risks, unknowns, recommendation, and attribution.

Every run is **replayable**. Export a `.cassette` file and rerun offline — no API key required for demos, tests, or CI.

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-role panel** | Parallel specialists (architecture, security, performance, QA, and more) each analyze the same input |
| **Decision Reports** | Structured output: consensus, disagreements, risks, unknowns, recommendation, and per-role attribution |
| **Fast & thorough modes** | `fast`: panel → judge. `thorough`: panel → anonymized peer review → judge |
| **Templates** | YAML-defined councils for PR review, architecture review, song writing, or your own workflows |
| **Outcome selection** | Choose deliverables: review report, implementation plan, merge verdict, ADR set, full song, and more |
| **Cassettes** | Record and replay LLM responses as portable `.cassette` files — keyless demos and CI |
| **Cost caps** | Per-run USD limits; runs fail cleanly when exceeded |
| **Web UI** | Compose runs, watch live deliberation via SSE, browse history, export cassettes |
| **CLI** | Pipe `gh pr diff`, run from files, view history, export reports |
| **MCP server** | Start async reviews from Cursor, Claude Code, or any MCP client |
| **Model overrides** | Pick models per role and judge; OpenRouter-backed |

---

## Quickstart (< 60s, keyless)

```bash
# Install
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/checkolo/agent-council.git && cd agent-council
uv sync --all-extras

# Replay a sample cassette (no API key)
uv run quorum replay cassettes/samples/demo-auth.cassette

# Run tests (no API key needed)
make test

# Start the web UI
make build-ui && uv run quorum serve
# → http://localhost:8000
```

---

## With an API key

Set your [OpenRouter](https://openrouter.ai/) key:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

```bash
# Review a PR diff from the terminal
gh pr diff | uv run quorum review --template pr-review

# Or from a file
uv run quorum run --template pr-review --file diff.patch --mode fast --max-cost 0.50

# Thorough architecture review with peer review phase
uv run quorum run -t architecture-review -f design.md --mode thorough

# Browse run history
uv run quorum history
uv run quorum show <run-id>
uv run quorum export <run-id> -o review.cassette
```

---

## Three surfaces

| Surface | Command | Best for |
|---------|---------|----------|
| **Web** | `quorum serve` | Compose runs, live deliberation, Decision Reports, cassette viewer |
| **CLI** | `quorum` | Daily driver, pipes, `gh pr diff`, scripting |
| **MCP** | `quorum serve --mcp` | Agent tools in Cursor / Claude Code |

See [docs/web-ui.md](docs/web-ui.md) and [docs/mcp.md](docs/mcp.md) for details.

---

## How it works

```
Task + Template → Panel (parallel) → [Peer Review] → Judge → Decision Report → Cassette
```

1. **Panel** — Each council member analyzes the input in parallel with a role-specific system prompt.
2. **Peer review** *(thorough mode)* — Members review anonymized peer outputs before synthesis.
3. **Judge** — A stronger model produces a structured Decision Report (JSON + markdown deliverable).
4. **Cassette** — The full run (inputs, events, report) is exportable for offline replay.

→ [Architecture guide](docs/architecture.md)

---

## Built-in templates

| Template | Roles | Default mode | Outcomes |
|----------|-------|--------------|----------|
| `pr-review` | Architect, Security, Performance, QA | fast | Review report, implementation plan, merge verdict |
| `architecture-review` | Architect, Security, Performance, QA | thorough | Review report, implementation plan, ADR set |
| `song-writer` | Lyricist, Melody, Producer, Critic | fast | Full song, lyrics only, hook demo |

List templates: `uv run quorum templates`

→ [Templates guide](docs/templates.md)

---

## Documentation

| Doc | Contents |
|-----|----------|
| [Architecture](docs/architecture.md) | Council engine, phases, Decision Report schema |
| [CLI reference](docs/cli.md) | All `quorum` commands and flags |
| [Templates](docs/templates.md) | Create and customize council templates |
| [Cassettes](docs/cassettes.md) | Record, replay, and share offline runs |
| [Web UI](docs/web-ui.md) | Dashboard, live runs, cassette viewer |
| [MCP](docs/mcp.md) | Agent integration tools |

---

## Development

```bash
make install      # uv sync
make dev          # FastAPI :8000 + Vite :5173
make test         # pytest on cassettes (keyless)
make lint         # ruff
make build-ui     # React → quorum/web/
make demo         # keyless recorded run
make eval         # eval harness
```

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key (optional for cassette replay) |
| `QUORUM_PANEL_MAX_TOKENS` | Max tokens per panel member (default: 4096) |
| `QUORUM_JUDGE_MAX_TOKENS` | Max tokens for judge (default: 131072; `0` = provider default) |

---

## License

MIT. No telemetry. BYOK (Bring Your Own Key via `OPENROUTER_API_KEY`).

---

<p align="center">
  <strong>Agent Council</strong> · by <strong>Planner Pannel</strong>
</p>
