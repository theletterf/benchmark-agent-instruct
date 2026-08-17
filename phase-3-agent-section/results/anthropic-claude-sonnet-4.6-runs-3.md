# Phase 3 — For agents intervention

## Question

Does adding a dedicated `For agents` section to otherwise unchanged documentation improve agent behavior?

## Corpus

Frozen authoritative OpenTelemetry documentation and migration guidance. The five control artifacts use coherent page sections rather than answer-only excerpts.

## Tasks

- **HTTP client request telemetry** — 6 independently scored decisions
- **HTTP server request telemetry** — 7 independently scored decisions
- **HTTP client duration histogram** — 5 independently scored decisions
- **Database client query telemetry** — 6 independently scored decisions
- **Java agent and SDK defaults** — 5 independently scored decisions

## Intervention

Condition A: normal documentation

Condition B: the same documentation plus one concise `For agents` synthesis

## Validation

A/B artifacts are accepted only when removing the marked agent block from B reproduces A byte-for-byte and every proposition has support in A.

## Results

| Condition | Responses | Decisions | Current/correct | Fully correct | Mixed | Historical | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A — Normal docs | 15 | 87 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| B — + For agents | 15 | 87 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |

## By task

| Task | Responses | Decisions | Current/correct | Fully correct | Mixed | Historical | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| database-client-telemetry | 6 | 36 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| http-client-duration | 6 | 30 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| http-client-telemetry | 6 | 36 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| http-server-telemetry | 6 | 42 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |
| java-agent-configuration | 6 | 30 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |

## By model

| Model | Responses | Decisions | Current/correct | Fully correct | Mixed | Historical | Invalid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic/claude-sonnet-4.6 | 30 | 174 | 100.0% | 100.0% | 0.0% | 0.0% | 0.0% |

## Effect

Decision-level difference: **+0.0 percentage points** (B − A).

## Token overhead

Normal docs, total across five artifacts: 38095 estimated tokens.
Agent sections, total: 793 estimated tokens.
Treatment artifacts, total: 38970 estimated tokens.
Descriptive efficiency: +0.00 percentage points per 100 additional estimated input tokens (using mean section cost).

| Task | Normal docs | Agent section | Treatment | Context increase |
| --- | ---: | ---: | ---: | ---: |
| http-client-telemetry | 7897 | 150 | 8063 | 2.10% |
| http-server-telemetry | 8003 | 154 | 8173 | 2.12% |
| http-client-duration | 10216 | 180 | 10413 | 1.93% |
| database-client-telemetry | 9113 | 158 | 9287 | 1.91% |
| java-agent-configuration | 2866 | 151 | 3034 | 5.86% |

## Interpretation

No meaningful benefit was detected under these tasks and models.

The intervention bundles repetition, synthesis, explicit recommendation, isolation, and audience targeting. This phase does not decompose them.

## Ceiling diagnostics

**CONTROL CEILING**

If controls saturate, first assess whether the complete bundle resembles documentation a real agent would receive; do not weaken correct documentation merely to create headroom.

## Comparison with earlier phases

- Phase 1 — fables: explicit recommendation strongly changed behavior, then ceiling.
- Phase 2 — SQLAlchemy/OpenTelemetry: ordinary focused documentation often corrected behavior to ceiling.
- Phase 3 — realistic normal docs vs the same docs plus `For agents`: tests whether the practical intervention adds value.

The phases are not statistically pooled.

## Caveats

- Token counts are stable four-UTF-8-bytes-per-token estimates; provider-reported counts are retained in result rows.
- Five tasks and three repetitions are a quick intervention test, not a broad population estimate.
- A detected effect would justify, but does not itself answer, later mechanism experiments.
- Input results: `phase-3-agent-section/results/anthropic-claude-sonnet-4.6-runs-3.jsonl`.
