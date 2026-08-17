# Experiment 2 — Structural isolation

## Question

Does isolating otherwise identical recommendation wording increase preferred-path compliance?

## Manipulation

The independent variable is **paragraph isolation**. Condition A is isolated paragraph; condition B is enmeshed prose. All other prompt components are held constant within each world.

## Setup

- Model(s): google/gemini-2.5-flash-lite
- Worlds: bellwater, lantern, messenger, orchard, well
- Calls: 30
- Temperature requested: 0.0

Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.

## Results

| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| A — isolated paragraph | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| B — enmeshed prose | 15 | 15 (100.0%) | 15 (100.0%) [79.6, 100.0] | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

## Effect

Preferred-path difference (B − A): +0.00 percentage points. Fisher's exact p = 1.0.

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
