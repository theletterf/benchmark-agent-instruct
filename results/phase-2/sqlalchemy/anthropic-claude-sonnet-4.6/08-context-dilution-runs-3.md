# Experiment 8 — Context dilution

## Research question

Does the recommendation remain effective with substantially more official context?

## Phase 1 analogue

Phase 1 Experiment 8 manipulated official context breadth in a fictional world. Phase 2 preserves that independent variable while using frozen SQLAlchemy 2.x documentation and executable ORM tasks.

## Real-document manipulation

Condition A: focused retrieval. Condition B: broad retrieval. The independent variable is official context breadth.

## Source material

SQLAlchemy 2.0.52; frozen official ORM SELECT, Session, migration, and Legacy Query documentation. Source URLs and SHA-256 hashes are recorded in the project source manifest.

## Prior calibration

No-documentation current-pattern selection: 80.0% (8/10).

## Results

| Condition | N | Current (Wilson 95%) | Legacy | Mixed | Unclassified |
|---|---:|---:|---:|---:|---:|
| A — focused retrieval | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |
| B — broad retrieval | 15 | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 | 0 |

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
| retrieve-all | B | 3 | 3 (100.0%) | 0 | 0 | 2 (66.7%) |

## Artifact token sizes

Approximate artifact tokens use the same character-based estimator before provider execution.

| Task | A tokens | B tokens | B vs A reduction | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| primary-key-lookup | 105 | 4867 | -4535.2% | 0.6978 | 0.5007 |
| retrieve-all | 151 | 4914 | -3154.3% | 0.7467 | 0.504 |
| filter-one | 160 | 4923 | -2976.9% | 0.6865 | 0.5025 |
| first-matching | 124 | 4886 | -3840.3% | 0.5416 | 0.4975 |
| join-filter | 126 | 4889 | -3780.2% | 0.5496 | 0.4977 |


## Functional correctness

Syntax success: 30/30. Runtime success: 29/30. Functional correctness: 29/30.

## Current vs legacy selection

API-family classification is AST-based and reported separately from executable correctness; working legacy answers remain legacy.

## Token usage

Provider-reported prompt tokens: 84,468. Completion tokens: 3,727.

## Ceiling diagnostics

No detectable difference under a ceiling condition (100% vs 100%).

## Interpretation

Interpret the direct contrast together with task-level variation and the prior calibration. Calibration is descriptive and is not a third randomized condition.

## Caveats

Five API decisions limit generalization. Temperature-zero repetitions may be correlated. Runtime success under pinned SQLite does not establish suitability for every database or application.
