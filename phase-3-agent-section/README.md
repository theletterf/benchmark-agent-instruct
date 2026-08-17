# Phase 3 — For agents intervention

This phase returns to the practical documentation intervention: does adding a concise `For agents` section to a normal documentation bundle improve task behavior?

It has exactly two conditions:

- **A — Normal documentation:** frozen, ordinary OpenTelemetry documentation bundles.
- **B — Exactly the same documentation + `For agents`:** the A artifact plus one short operational synthesis already supported by A.

The five tasks cover HTTP client spans, HTTP server spans, HTTP client duration metrics, database client spans, and Java agent/SDK defaults. There are 29 independently scored decisions. No no-documentation condition, mechanism decomposition, LLM judge, or paid result is included here.

Frozen sources, source hashes, task definitions, decision manifests, A/B artifacts, human-readable diffs, proposition-support manifests, and token counts all live in this directory. Validation fails if source bytes change, task/source artifacts drift, B changes any normal-documentation byte, or a proposition lacks support in A.

Commands:

```bash
python -m benchmark agent-section inspect opentelemetry
python -m benchmark agent-section diff opentelemetry
python -m benchmark agent-section validate opentelemetry
python -m benchmark agent-section run opentelemetry --model anthropic/claude-sonnet-4.6 --smoke
python -m benchmark agent-section run opentelemetry --model anthropic/claude-sonnet-4.6 --runs 3
python -m benchmark agent-section report phase-3-agent-section/results/<file>.jsonl
```

Use `--dry-run` on either run command to verify its call plan without contacting OpenRouter.
