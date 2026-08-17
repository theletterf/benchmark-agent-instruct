# Experiment 6 — Semantic compression

## Question

Can human-oriented narrative be removed without reducing behavioral compliance?

## Manipulation

The independent variable is **semantic compression**. Condition A is full document; condition B is semantically compressed document. All other prompt components are held constant within each world.

## Setup

- Model(s): google/gemini-2.5-flash-lite
- Worlds: bellwater, lantern, messenger, orchard, well
- Calls: 30
- Temperature requested: 0.0

Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.

## Results

| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| A — full document | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| B — semantically compressed document | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Effect

Preferred-path difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

## Compression sizes

| World | A tokens | B tokens | Reduction B vs A | A recommendation position | B recommendation position |
|---|---:|---:|---:|---:|---:|
| bellwater | 1137 | 160 | 85.9% | 0.8581 | 0.6248 |
| lantern | 1142 | 165 | 85.6% | 0.8581 | 0.6328 |
| messenger | 1144 | 167 | 85.4% | 0.8574 | 0.6301 |
| orchard | 1138 | 165 | 85.5% | 0.8581 | 0.6364 |
| well | 1136 | 161 | 85.8% | 0.8587 | 0.6324 |

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
