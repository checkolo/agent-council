# CLI Reference

The Agent Council CLI is invoked as `quorum`. Install via `uv sync` from the repo root.

## Global

```bash
uv run quorum --help
uv run quorum version
uv run quorum self-test    # Verify SQLite storage
```

## Run a council review

```bash
uv run quorum run [OPTIONS]
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--template` | `-t` | `pr-review` | Template name (see `templates/`) |
| `--file` | `-f` | — | Input file path |
| `--mode` | `-m` | `fast` | `fast` or `thorough` |
| `--max-cost` | | template default | Max spend in USD |
| `--recorded` | | false | Replay from recorded cassettes |
| `--record` | | false | Record LLM responses to cassettes |
| `--out` | `-o` | — | Save Decision Report as markdown |

**Input sources:** `--file`, stdin pipe, or interactive (will prompt for a file).

```bash
# From file
uv run quorum run -t pr-review -f tests/fixtures/sample.diff

# From pipe
gh pr diff 42 | uv run quorum review

# Record for offline replay
uv run quorum run -t song-writer -f brief.txt --record

# Keyless replay
uv run quorum run -t pr-review -f sample.diff --recorded
```

## Review alias

`quorum review` is an alias for `quorum run`, optimized for piping diffs:

```bash
gh pr diff | uv run quorum review --template pr-review --mode fast
```

## Templates

```bash
uv run quorum templates
```

Lists all YAML templates with roles, default mode, and cost cap.

## Run history

```bash
uv run quorum history [--limit N]   # default: 20
uv run quorum show <run-id>
uv run quorum export <run-id> [-o output.cassette]
```

## Cassettes

```bash
uv run quorum replay path/to/run.cassette
```

Replays a exported cassette offline and renders the Decision Report.

## Single LLM call (testing)

```bash
uv run quorum call <model> "<message>" [--recorded] [--record]
```

Useful for verifying cassette recording without running a full council.

## Eval harness

```bash
uv run quorum eval [--suite evals/coding-questions.yaml]
```

Runs the eval suite (recorded mode) and writes results to `evals/latest.md`.

## Web & MCP server

```bash
uv run quorum serve [--host 0.0.0.0] [--port 8000]
uv run quorum serve --mcp    # MCP stdio server instead of HTTP
```

Or via Makefile:

```bash
make serve    # builds UI + starts server
make dev      # FastAPI :8000 + Vite :5173 with hot reload
```

## Environment

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Required for live runs; optional with `--recorded` |
| `QUORUM_PANEL_MAX_TOKENS` | Panel member token limit |
| `QUORUM_JUDGE_MAX_TOKENS` | Judge token limit (`0` = omit) |
