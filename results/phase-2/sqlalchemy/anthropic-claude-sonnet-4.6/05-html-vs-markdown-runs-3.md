# Experiment 5 — HTML vs Markdown

## Research question

Does raw representation affect current-pattern selection when semantic content is equivalent?

## Phase 1 analogue

Phase 1 Experiment 5 manipulated raw markup representation in a fictional world. Phase 2 preserves that independent variable while using frozen SQLAlchemy 2.x documentation and executable ORM tasks.

## Real-document manipulation

Condition A: HTML. Condition B: Markdown. The independent variable is raw markup representation.

## Source material

SQLAlchemy 2.0.52; frozen official ORM SELECT, Session, migration, and Legacy Query documentation. Source URLs and SHA-256 hashes are recorded in the project source manifest.

## Prior calibration

No-documentation current-pattern selection: 80.0% (8/10).

## Results

| Condition | N | Current (Wilson 95%) | Legacy | Mixed | Unclassified |
|---|---:|---:|---:|---:|---:|
| A — HTML | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |
| B — Markdown | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |

Current-pattern difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## By task

| Task | Condition | N | Current | Legacy | Mixed | Functional |
|---|---|---:|---:|---:|---:|---:|
| filter-one | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| filter-one | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| join-filter | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| join-filter | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |

## Artifact token sizes

Approximate artifact tokens use the same character-based estimator before provider execution.

| Task | A tokens | B tokens | B vs A reduction | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| primary-key-lookup | 120 | 117 | 2.5% | n/a | 0.729 |
| retrieve-all | 169 | 163 | 3.6% | n/a | 0.7653 |
| filter-one | 179 | 172 | 3.9% | n/a | 0.7085 |
| first-matching | 139 | 136 | 2.2% | n/a | 0.5823 |
| join-filter | 142 | 138 | 2.8% | n/a | 0.5888 |


## Functional correctness

Syntax success: 30/30. Runtime success: 30/30. Functional correctness: 30/30.

## Current vs legacy selection

API-family classification is AST-based and reported separately from executable correctness; working legacy answers remain legacy.

## Token usage

Provider-reported prompt tokens: 9,360. Completion tokens: 1,710.

## Ceiling diagnostics

No detectable difference under a ceiling condition (100% vs 100%).

## Interpretation

Interpret the direct contrast together with task-level variation and the prior calibration. Calibration is descriptive and is not a third randomized condition.

## Caveats

Five API decisions limit generalization. Temperature-zero repetitions may be correlated. Runtime success under pinned SQLite does not establish suitability for every database or application.
