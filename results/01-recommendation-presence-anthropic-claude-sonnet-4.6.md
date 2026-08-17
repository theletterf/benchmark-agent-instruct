# Experiment 1 — Recommendation presence

## Question

Does adding an explicit recommendation change which valid procedure is selected?

## Manipulation

The independent variable is **recommendation presence**. Condition A is neutral; condition B is recommendation present. All other prompt components are held constant within each world.

## Setup

- Model(s): anthropic/claude-sonnet-4.6
- Worlds: bellwater, lantern, messenger, orchard, well
- Calls: 30
- Temperature requested: 0.0

Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.

## Results

| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| A — neutral | 15 | 15 (100.0%) | 5 (33.3%) [15.2, 58.3] | 10 (66.7%) | 0 (0.0%) | 0 (0.0%) |
| B — recommendation present | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Effect

Preferred-path difference (B − A): +66.67 percentage points. Fisher's exact p = 0.0002.

## By world

| Model | World | Condition | N | Correct | Preferred | Alternative | Mixed | Invalid |
|---|---|---|---:|---:|---:|---:|---:|---:|
| anthropic/claude-sonnet-4.6 | bellwater | A | 3 | 3 (100.0%) | 0 (0.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | bellwater | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | lantern | A | 3 | 3 (100.0%) | 0 (0.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | lantern | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | messenger | A | 3 | 3 (100.0%) | 0 (0.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | messenger | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | orchard | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | orchard | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | well | A | 3 | 3 (100.0%) | 2 (66.7%) | 1 (33.3%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | well | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Interpretation

Interpret the direct two-condition contrast together with its world-level pattern. A null aggregate remains informative and should not cause later experiments to be skipped.

## Caveats

Five fictional worlds limit generalization. Repeated deterministic calls may be correlated, provider routing can vary, and approximate artifact token counts use a character-based estimator while run rows retain provider-reported usage when available.
