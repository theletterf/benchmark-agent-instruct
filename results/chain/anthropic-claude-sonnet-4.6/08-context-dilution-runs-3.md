# Experiment 8 — Context dilution

## Question

Does an isolated recommendation retain its influence in much more irrelevant context?

## Manipulation

The independent variable is **irrelevant context length**. Condition A is short context; condition B is long context. All other prompt components are held constant within each world.

## Setup

- Model(s): anthropic/claude-sonnet-4.6
- Worlds: bellwater, lantern, messenger, orchard, well
- Calls: 30
- Temperature requested: 0.0

Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.

## Results

| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| A — short context | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| B — long context | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Effect

Preferred-path difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## Context sizes and recommendation position

| World | A tokens | B tokens | Reduction B vs A | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| bellwater | 758 | 5876 | -675.2% | 0.5383 | 0.5049 |
| lantern | 762 | 5896 | -673.8% | 0.5386 | 0.505 |
| messenger | 764 | 5896 | -671.7% | 0.538 | 0.5049 |
| orchard | 759 | 5868 | -673.1% | 0.5384 | 0.505 |
| well | 757 | 5873 | -675.8% | 0.5387 | 0.505 |

## By world

| Model | World | Condition | N | Correct | Preferred | Alternative | Mixed | Invalid |
|---|---|---|---:|---:|---:|---:|---:|---:|
| anthropic/claude-sonnet-4.6 | bellwater | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | bellwater | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | lantern | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | lantern | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | messenger | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | messenger | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | orchard | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | orchard | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | well | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| anthropic/claude-sonnet-4.6 | well | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Interpretation

Interpret the direct two-condition contrast together with its world-level pattern. A null aggregate remains informative and should not cause later experiments to be skipped.

## Caveats

Five fictional worlds limit generalization. Repeated deterministic calls may be correlated, provider routing can vary, and approximate artifact token counts use a character-based estimator while run rows retain provider-reported usage when available.
