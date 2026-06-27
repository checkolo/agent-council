# Templates

Templates define **which council members** convene, **which judge model** synthesizes, and **what deliverable** the judge produces.

Templates live in `templates/*.yaml` at the repo root.

## Anatomy of a template

```yaml
name: pr-review
description: Review a pull request diff with architecture, security, performance, and QA lenses.
roles:
  - architect
  - security
  - performance
  - qa
judge_model: anthropic/claude-sonnet-4
mode: fast
max_cost_usd: 0.50
default_outcome: review-report
outcomes:
  - id: review-report
    label: Review report
    description: Consensus, disagreements, risks, and recommendation
    instruction: |
      Produce a standard code review DecisionReport with consensus, disagreements,
      risks, unknowns, recommendation, and attribution.
  - id: merge-verdict
    label: Merge verdict
    description: Clear approve / request-changes / block decision
    instruction: |
      Your primary deliverable MUST be an explicit merge verdict (APPROVE,
      REQUEST CHANGES, or BLOCK) with rationale and required follow-ups.
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Unique identifier (matches filename without `.yaml`) |
| `description` | no | Shown in web UI and `quorum templates` |
| `roles` | yes | List of role keys from `quorum/council/roles.py` |
| `judge_model` | no | OpenRouter model slug (default: `anthropic/claude-sonnet-4`) |
| `mode` | no | Default mode: `fast` or `thorough` |
| `max_cost_usd` | no | Default cost cap (default: `0.50`) |
| `default_outcome` | no | Outcome ID selected by default |
| `outcomes` | no | Deliverable options the judge can produce |

## Available roles

Defined in `quorum/council/roles.py`:

| Key | Display name | Focus |
|-----|--------------|-------|
| `architect` | Architect | Module boundaries, coupling, evolution |
| `security` | Security Reviewer | Threat model, auth, secrets, input validation |
| `performance` | Performance Engineer | Hot paths, complexity, caching, concurrency |
| `qa` | QA Engineer | Testability, edge cases, observability |
| `lyricist` | Lyricist | Narrative, rhyme, imagery, hooks |
| `melody` | Melody Composer | Melodic contour, phrasing, key/mode |
| `producer` | Producer | Structure, dynamics, arrangement |
| `critic` | Music Critic | Market appeal, originality, audience fit |

Each role has suggested models for the web UI model picker.

## Built-in templates

### `pr-review`

Four engineering lenses on a code diff. Default mode: **fast**. Outcomes: review report, implementation plan, merge verdict.

### `architecture-review`

Same engineering roles, default mode: **thorough** (includes peer review). Higher cost cap ($1.00). Outcomes include an ADR set.

### `song-writer`

Creative council: Lyricist, Melody, Producer, Critic. Demonstrates Agent Council beyond code review. Outcomes: full song, lyrics only, hook demo.

## Creating a custom template

1. Add a new file: `templates/my-template.yaml`
2. Pick roles from the table above (or add new roles in `roles.py`)
3. Define at least one outcome with a clear `instruction` for the judge
4. Verify: `uv run quorum templates`
5. Run: `uv run quorum run -t my-template -f input.txt`

## Subsetting roles

In the web UI and API, you can pass a subset of the template's roles (minimum one). Invalid role keys are rejected.

```json
POST /api/runs
{
  "template": "pr-review",
  "input": "...",
  "roles": ["architect", "security"]
}
```

## Outcome selection

The `desired_outcome` field (CLI/API) selects which outcome instruction the judge receives. The judge is instructed to **deliver the outcome even when the panel disagrees** — disagreements are noted but must not block the primary deliverable.
