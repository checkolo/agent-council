# Architecture

Agent Council (package name: `quorum`) is a three-phase deliberation engine backed by OpenRouter, SQLite storage, and a React web UI.

## Pipeline

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Input     │────▶│  Panel (parallel) │────▶│ Peer Review │────▶│     Judge       │
│ + Template  │     │  N role members   │     │ (thorough)  │     │  synthesizes    │
└─────────────┘     └──────────────────┘     └─────────────┘     └─────────────────┘
                           │                        │                      │
                           └────────────────────────┴──────────────────────┘
                                                    │
                                                    ▼
                                          ┌─────────────────┐
                                          │ Decision Report │
                                          │ + Cassette      │
                                          └─────────────────┘
```

### Phase 1: Panel

Each role in the template runs **in parallel**. Every member receives:

- A role-specific system prompt (e.g. Architect focuses on module boundaries and coupling)
- The full task input (diff, design doc, brief, etc.)

Panel members use lighter/faster models by default. Outputs are streamed to the UI via SSE events (`panel.token`, `panel.done`).

### Phase 2: Peer review (thorough mode only)

In `thorough` mode, each panel member reviews **anonymized** outputs from the other members. This reduces anchoring on role identity and surfaces cross-cutting disagreements before synthesis.

Peer review events: `review.token`, `review.done`.

### Phase 3: Judge

A stronger model (configurable per template) receives:

- All panel outputs (with role attribution)
- Peer review text (if thorough)
- An **outcome instruction** (e.g. "produce a merge verdict" or "write a full song")

The judge emits a structured **Decision Report** — ideally as JSON inside a markdown fence. If parsing fails, a markdown fallback is used with an automatic retry when the deliverable is too short.

Judge events: `judge.token`, `judge.done`, then `run.done`.

## Decision Report schema

| Field | Description |
|-------|-------------|
| `deliverable` | Primary output (review text, song lyrics, plan, etc.) |
| `consensus` | Points all panel members agreed on |
| `disagreements` | Topics where members diverged, with positions and resolution |
| `risks` | Identified risks with severity (`blocker`, `major`, `minor`, `nit`) |
| `unknowns` | Open questions that need human input |
| `recommendation` | Final action with supporting evidence |
| `attribution` | Which role contributed which idea |
| `member_outputs` | Raw panel member responses |
| `peer_reviews` | Raw peer review responses (thorough mode) |
| `cost_usd` | Total OpenRouter cost for the run |
| `duration_ms` | Wall-clock duration |

## Modes

| Mode | Phases | Typical use |
|------|--------|-------------|
| `fast` | Panel → Judge | PR reviews, quick feedback, agent workflows |
| `thorough` | Panel → Peer Review → Judge | Architecture reviews, high-stakes decisions |

## Core modules

| Path | Role |
|------|------|
| `quorum/council/engine.py` | Orchestrates panel, peer review, judge |
| `quorum/council/roles.py` | Role definitions and system prompts |
| `quorum/council/decision.py` | Decision Report models and parsing |
| `quorum/council/prompts.py` | Panel, peer, and judge prompt templates |
| `quorum/llm/openrouter.py` | OpenRouter client with cost tracking |
| `quorum/llm/cassettes.py` | Record/replay LLM responses |
| `quorum/storage/sqlite.py` | Run history and event persistence |
| `quorum/api/server.py` | FastAPI REST + SSE + SPA mount |
| `quorum/mcp/server.py` | MCP tool server for agents |
| `templates/*.yaml` | Council template definitions |

## Cost control

Each run has a `max_cost_usd` cap (from template default or CLI/API override). Before every LLM call, the engine checks accumulated cost against the cap and raises `CostCapExceeded` if exceeded.

## Real-time events

The web UI subscribes to `/api/runs/{run_id}/stream` (Server-Sent Events). Events are persisted to SQLite so late joiners can replay from any offset.

Event types: `panel.token`, `panel.done`, `panel.partial`, `review.token`, `review.done`, `judge.token`, `judge.done`, `run.done`.
