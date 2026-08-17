# Experiment 7 — Stronger compression

## Question

How much further can semantic compression go before behavior changes?

## Manipulation

The independent variable is **compression strength**. Condition A is moderate compression; condition B is strong compression. All other prompt components are held constant within each world.

## Setup

- Model(s): google/gemini-2.5-flash-lite
- Worlds: bellwater, lantern, messenger, orchard, well
- Calls: 30
- Temperature requested: 0.0

Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.

## Results

| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| A — moderate compression | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| B — strong compression | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Effect

Preferred-path difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## Compression sizes

| World | A tokens | B tokens | Reduction B vs A | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| bellwater | 160 | 105 | 34.4% | 0.6248 | 0.7286 |
| lantern | 165 | 110 | 33.3% | 0.6328 | 0.7386 |
| messenger | 167 | 111 | 33.5% | 0.6301 | 0.7381 |
| orchard | 165 | 112 | 32.1% | 0.6364 | 0.7371 |
| well | 161 | 107 | 33.5% | 0.6324 | 0.7336 |

## By world

| Model | World | Condition | N | Correct | Preferred | Alternative | Mixed | Invalid |
|---|---|---|---:|---:|---:|---:|---:|---:|
| google/gemini-2.5-flash-lite | bellwater | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | bellwater | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | lantern | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | lantern | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | messenger | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | messenger | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | orchard | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | orchard | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | well | A | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| google/gemini-2.5-flash-lite | well | B | 3 | 3 (100.0%) | 3 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Interpretation

Interpret the direct two-condition contrast together with its world-level pattern. A null aggregate remains informative and should not cause later experiments to be skipped.

## Caveats

Five fictional worlds limit generalization. Repeated deterministic calls may be correlated, provider routing can vary, and approximate artifact token counts use a character-based estimator while run rows retain provider-reported usage when available.
