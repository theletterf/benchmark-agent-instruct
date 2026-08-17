# Experiment 1 — Recommendation presence

## Research question

Does adding an explicit recommendation increase current-pattern selection over official documentation alone?

## Phase 1 analogue

Phase 1 Experiment 1 manipulated recommendation presence in a fictional world. Phase 2 preserves that independent variable while using frozen SQLAlchemy 2.x documentation and executable ORM tasks.

## Real-document manipulation

Condition A: official documentation. Condition B: official documentation plus recommendation. The independent variable is recommendation presence.

## Source material

SQLAlchemy 2.0.52; frozen official ORM SELECT, Session, migration, and Legacy Query documentation. Source URLs and SHA-256 hashes are recorded in the project source manifest.

## Prior calibration

No-documentation current-pattern selection: 80.0% (8/10).

## Results

| Condition | N | Current (Wilson 95%) | Legacy | Mixed | Unclassified |
|---|---:|---:|---:|---:|---:|
| A — official documentation | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |
| B — official documentation plus recommendation | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |

Current-pattern difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## By task

| Task | Condition | N | Current | Legacy | Mixed | Functional |
|---|---|---:|---:|---:|---:|---:|
| filter-one | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| filter-one | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| first-matching | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| join-filter | A | 3 | 3 (100.0%) | 0 | 0 | 0 (0.0%) |
| join-filter | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| primary-key-lookup | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | A | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |
| retrieve-all | B | 3 | 3 (100.0%) | 0 | 0 | 3 (100.0%) |


## Functional correctness

Syntax success: 30/30. Runtime success: 27/30. Functional correctness: 27/30.

## Current vs legacy selection

API-family classification is AST-based and reported separately from executable correctness; working legacy answers remain legacy.

## Token usage

Provider-reported prompt tokens: 7,935. Completion tokens: 1,947.

## Ceiling diagnostics

No detectable difference under a ceiling condition (100% vs 100%).

## Interpretation

Interpret the direct contrast together with task-level variation and the prior calibration. Calibration is descriptive and is not a third randomized condition.

## Caveats

Five API decisions limit generalization. Temperature-zero repetitions may be correlated. Runtime success under pinned SQLite does not establish suitability for every database or application.
