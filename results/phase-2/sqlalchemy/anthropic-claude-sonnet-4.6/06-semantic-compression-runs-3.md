# Experiment 6 — Semantic compression

## Research question

Can human-oriented documentation be compressed while preserving current-pattern steering?

## Phase 1 analogue

Phase 1 Experiment 6 manipulated semantic compression in a fictional world. Phase 2 preserves that independent variable while using frozen SQLAlchemy 2.x documentation and executable ORM tasks.

## Real-document manipulation

Condition A: full documentation. Condition B: semantically compressed Markdown. The independent variable is semantic compression.

## Source material

SQLAlchemy 2.0.52; frozen official ORM SELECT, Session, migration, and Legacy Query documentation. Source URLs and SHA-256 hashes are recorded in the project source manifest.

## Prior calibration

No-documentation current-pattern selection: 80.0% (8/10).

## Results

| Condition | N | Current (Wilson 95%) | Legacy | Mixed | Unclassified |
|---|---:|---:|---:|---:|---:|
| A — full documentation | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |
| B — semantically compressed Markdown | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |

Current-pattern difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## By task

| Task | Condition | N | Current | Legacy | Mixed | Functional |
|---|---|---:|---:|---:|---:|---:|
| filter-one | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| filter-one | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | A | 3 | 3 (100.0%) | 0 | 0 | 0 (0.0%) |
| first-matching | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| join-filter | A | 3 | 3 (100.0%) | 0 | 0 | 0 (0.0%) |
| join-filter | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |

## Artifact token sizes

Approximate artifact tokens use the same character-based estimator before provider execution.

| Task | A tokens | B tokens | B vs A reduction | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| primary-key-lookup | 386 | 166 | 57.0% | 0.9184 | n/a |
| retrieve-all | 430 | 167 | 61.2% | 0.911 | n/a |
| filter-one | 443 | 188 | 57.6% | 0.887 | n/a |
| first-matching | 415 | 200 | 51.8% | 0.8636 | n/a |
| join-filter | 421 | 207 | 50.8% | 0.865 | n/a |


## Functional correctness

Syntax success: 30/30. Runtime success: 24/30. Functional correctness: 24/30.

## Current vs legacy selection

API-family classification is AST-based and reported separately from executable correctness; working legacy answers remain legacy.

## Token usage

Provider-reported prompt tokens: 13,059. Completion tokens: 2,491.

## Ceiling diagnostics

No detectable difference under a ceiling condition (100% vs 100%).

## Interpretation

Interpret the direct contrast together with task-level variation and the prior calibration. Calibration is descriptive and is not a third randomized condition.

## Caveats

Five API decisions limit generalization. Temperature-zero repetitions may be correlated. Runtime success under pinned SQLite does not establish suitability for every database or application.
