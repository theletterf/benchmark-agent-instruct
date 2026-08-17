# Pinecone AI-audience heading replication

This is a focused label-only pilot derived from the frozen Pinecone Quickstart source retrieved on 2026-08-17. It is not part of the fable, SQLAlchemy, OpenTelemetry, or Phase 3 agent-section studies.

The three conditions contain identical current Pinecone quickstart documentation. They differ only in section hierarchy/heading:

- N: no section heading
- G: `## Recommended quickstart`
- AI: `## For AI agents and LLMs`

The task asks for an integrated-embedding quickstart function. Deterministic scoring records four current-versus-alternative API decisions: model-based index creation, record ingestion, text search, and text inputs.

The original two-condition generic-versus-AI-heading result remains preserved in `results/anthropic-claude-sonnet-4.6-runs-3.*`. The three-condition run, which adds the no-section control, is stored separately as `results/anthropic-claude-sonnet-4.6-with-no-section-runs-3.*`.

```bash
python -m benchmark pinecone-label validate
python -m benchmark pinecone-label diff
python -m benchmark pinecone-label run --model anthropic/claude-sonnet-4.6 --runs 3
```
