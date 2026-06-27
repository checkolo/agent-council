# Cassettes

Cassettes make Agent Council runs **portable and replayable**. A `.cassette` file captures the full run — input, template, events, and Decision Report — so you can demo, test, and share without calling LLMs again.

## What is a cassette?

A `.cassette` is a ZIP archive containing:

- `manifest.json` — version, export timestamp, run ID, template
- `run.json` — full run data including `decision_report` and `events`

Individual LLM responses are also recorded under `cassettes/recordings/` as JSON files keyed by request hash (used during `--recorded` replay).

## Modes

| Mode | Flag / UI | Behavior |
|------|-----------|----------|
| **Live** | default | Calls OpenRouter with your API key |
| **Record** | `--record` | Live calls + saves responses to cassettes |
| **Replay** | `--recorded` | Matches requests against recorded responses; no API key needed |

If `OPENROUTER_API_KEY` is unset, the client automatically falls back to recorded mode.

## CLI usage

```bash
# Record a run for later replay
uv run quorum run -t pr-review -f diff.patch --record

# Replay without an API key
uv run quorum run -t pr-review -f diff.patch --recorded

# Export an existing run
uv run quorum export <run-id> -o my-review.cassette

# View a cassette offline
uv run quorum replay my-review.cassette
```

Every `quorum run` also writes a cassette to `cassettes/<run-id>.cassette` automatically.

## Web UI

The composer includes a **Cassette mode** selector:

- **Live** — requires `OPENROUTER_API_KEY` on the server
- **Replay** — uses recorded responses (auto-selected when no key is configured)

Upload and inspect cassettes on the **Cassette Viewer** page (`/cassette`).

## Sample cassettes

Pre-built samples ship in `cassettes/samples/`:

```bash
uv run quorum replay cassettes/samples/demo-auth.cassette
uv run quorum replay cassettes/samples/demo-arch.cassette
```

The API exposes these at `GET /api/cassettes/samples/{name}` for the web UI.

## CI and testing

The test suite runs keyless against recorded cassettes:

```bash
make test
```

This makes Agent Council suitable for CI pipelines that validate parsing, storage, and API behavior without network calls or secrets.

## Sharing

Export from CLI or download from the web UI (`GET /api/runs/{run_id}/export`). Share the `.cassette` file — recipients can replay with `quorum replay` or upload to the Cassette Viewer.
