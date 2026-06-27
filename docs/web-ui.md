# Web UI

The Agent Council web app is a React SPA served by FastAPI at `http://localhost:8000` after `make build-ui && uv run quorum serve`.

For development with hot reload: `make dev` (API on `:8000`, Vite on `:5173`).

## Pages

### Dashboard (`/`)

Browse past council runs. Filter by template or status. Active runs auto-refresh every 2 seconds. Export cassettes or open a run for details.

### New Run (`/new`)

Compose a council session:

- **Template** — pr-review, architecture-review, song-writer, or custom
- **Input** — paste text, drop a file, or load a demo sample
- **Mode** — fast or thorough
- **Cost cap** — max USD spend
- **Cassette mode** — live, record, or replay
- **Council members** — toggle which roles participate
- **Outcome** — choose the judge deliverable (review report, merge verdict, full song, etc.)
- **Model overrides** — pick OpenRouter models per role and judge

Submit starts a background run and navigates to the live view.

**Replay from history:** `?replay=<run-id>` pre-fills input from a previous run for a free replay.

### Run View (`/runs/:id`)

Watch deliberation in real time via SSE:

1. **Panel phase** — tabbed member outputs stream in as each role completes
2. **Peer review phase** — *(thorough mode)* anonymized cross-reviews
3. **Judge phase** — verdict and deliverable stream in
4. **Decision Report** — consensus, disagreements, risks, unknowns, recommendation, attribution

Toggle **identity** to show or hide which model powered each role.

Export the run as a `.cassette` when complete.

### Cassette Viewer (`/cassette`)

Upload a `.cassette` file to inspect a past run offline — no server-side LLM calls.

## API endpoints

The UI consumes these REST and SSE routes:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Status, version, `has_api_key` |
| GET | `/api/templates` | All templates with role details and outcomes |
| GET | `/api/models` | Available judge models |
| GET | `/api/demo/samples` | Demo inputs per template |
| POST | `/api/runs` | Start a run (returns `run_id`) |
| GET | `/api/runs` | List runs (filterable) |
| GET | `/api/runs/{id}` | Run details + Decision Report |
| GET | `/api/runs/{id}/stream` | SSE event stream |
| GET | `/api/runs/{id}/export` | Download `.cassette` |
| POST | `/api/cassettes/view` | Upload and parse a cassette |

## Building

```bash
cd web && npm ci && npm run build
make build-ui   # copies dist/ → quorum/web/
```

The FastAPI app mounts `quorum/web/` as static files at `/`.
