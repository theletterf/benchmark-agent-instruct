# Experiment 5 — HTML vs Markdown

## Question

Does raw document representation affect compliance when textual content is equivalent?

## Manipulation

The independent variable is **raw markup representation**. Condition A is HTML; condition B is Markdown. All other prompt components are held constant within each world.

## Setup

- Model(s): anthropic/claude-sonnet-4.6
- Worlds: bellwater, lantern, messenger, orchard, well
- Calls: 30
- Temperature requested: 0.0

Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.

## Results

| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| A — HTML | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| B — Markdown | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Effect

Preferred-path difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## Representation sizes

| World | A tokens | B tokens | Reduction B vs A | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| bellwater | 212 | 191 | 9.9% | n/a | 0.6868 |
| lantern | 220 | 199 | 9.5% | n/a | 0.696 |
| messenger | 222 | 201 | 9.5% | n/a | 0.6929 |
| orchard | 220 | 199 | 9.5% | n/a | 0.6985 |
| well | 215 | 194 | 9.8% | n/a | 0.6951 |

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
