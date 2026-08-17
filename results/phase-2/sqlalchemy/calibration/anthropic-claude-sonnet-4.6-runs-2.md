# SQLAlchemy prior calibration

Model: anthropic/claude-sonnet-4.6

Task-only prompts; no documentation was supplied. This diagnostic is not Experiment 0.

| Task | N | Current | Legacy | Mixed | Headroom warning |
|---|---:|---:|---:|---:|---|
| primary-key-lookup | 2 | 2 (100.0%) | 0 | 0 | weak (≥80% current) |
| retrieve-all | 2 | 2 (100.0%) | 0 | 0 | weak (≥80% current) |
| filter-one | 2 | 2 (100.0%) | 0 | 0 | weak (≥80% current) |
| first-matching | 2 | 2 (100.0%) | 0 | 0 | weak (≥80% current) |
| join-filter | 2 | 0 (0.0%) | 2 | 0 | available |

## Headroom assessment

At least one task retains behavioral headroom; the main Phase 2 chain may proceed without changing frozen prompts.
