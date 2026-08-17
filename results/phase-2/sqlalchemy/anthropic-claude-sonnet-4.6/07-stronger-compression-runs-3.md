# Experiment 7 — Stronger compression

## Research question

Can the compressed representation be reduced further without losing corrective effect?

## Phase 1 analogue

Phase 1 Experiment 7 manipulated compression strength in a fictional world. Phase 2 preserves that independent variable while using frozen SQLAlchemy 2.x documentation and executable ORM tasks.

## Real-document manipulation

Condition A: moderate compression. Condition B: strong compression. The independent variable is compression strength.

## Source material

SQLAlchemy 2.0.52; frozen official ORM SELECT, Session, migration, and Legacy Query documentation. Source URLs and SHA-256 hashes are recorded in the project source manifest.

## Prior calibration

No-documentation current-pattern selection: 80.0% (8/10).

## Results

| Condition | N | Current (Wilson 95%) | Legacy | Mixed | Unclassified |
|---|---:|---:|---:|---:|---:|
| A — moderate compression | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |
| B — strong compression | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |

Current-pattern difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## By task

| Task | Condition | N | Current | Legacy | Mixed | Functional |
|---|---|---:|---:|---:|---:|---:|
| filter-one | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| filter-one | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| join-filter | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| join-filter | B | 3 | 3 (100.0%) | 0 | 0 | 2 (66.7%) |
| primary-key-lookup | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |

## Artifact token sizes

Approximate artifact tokens use the same character-based estimator before provider execution.

| Task | A tokens | B tokens | B vs A reduction | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| primary-key-lookup | 166 | 99 | 40.4% | n/a | n/a |
| retrieve-all | 167 | 100 | 40.1% | n/a | n/a |
| filter-one | 188 | 120 | 36.2% | n/a | n/a |
| first-matching | 200 | 132 | 34.0% | n/a | n/a |
| join-filter | 207 | 140 | 32.4% | n/a | n/a |


## Functional correctness

Syntax success: 30/30. Runtime success: 29/30. Functional correctness: 29/30.

## Current vs legacy selection

API-family classification is AST-based and reported separately from executable correctness; working legacy answers remain legacy.

## Token usage

Provider-reported prompt tokens: 8,721. Completion tokens: 1,689.

## Ceiling diagnostics

No detectable difference under a ceiling condition (100% vs 100%).

## Interpretation

Interpret the direct contrast together with task-level variation and the prior calibration. Calibration is descriptive and is not a third randomized condition.

## Caveats

Five API decisions limit generalization. Temperature-zero repetitions may be correlated. Runtime success under pinned SQLite does not establish suitability for every database or application.
