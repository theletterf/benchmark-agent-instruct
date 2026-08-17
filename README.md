# Documentation behavior benchmark

This repository tests a narrow question: which properties of documentation change the behavior of an LLM asked to act from that documentation? It keeps frozen sources, artifacts, deterministic scoring, raw provider output, and reports so that each result can be inspected and reproduced.

The work is organized as a sequence of research phases. Earlier artifacts and results are never rewritten to fit later hypotheses.

## Repository map

```text
benchmark/                         Shared CLI, runners, OpenRouter client, scoring, reports
worlds-v1/                         Frozen five-world synthetic corpus
experiments/                       Phase 1 fable experiments and historical pilot
results/                           Phase 1 JSONL, CSV, and Markdown reports
phase-2-real-docs/                 Real-document candidate-selection framework and results
  projects/sqlalchemy/             Preserved negative selection result
  projects/opentelemetry/          Preserved negative selection result
  experiments/                     Frozen nine-experiment real-doc templates
phase-3-agent-section/             OpenTelemetry `For agents` intervention and follow-ups
phase-4-pinecone-label/            Narrow Pinecone section-heading pilot
tests/                             Deterministic unit and integration tests
```

Each runnable study keeps its inputs alongside its outputs:

```text
sources/                           Frozen upstream documents and source manifests
tasks/ or worlds-v1/               Experimental units and task prompts
artifacts/                         Frozen condition documents
manifests/                         Hashes, proposition/decision manifests, metadata
results/                           Raw JSONL plus generated reports
```

`.env` is ignored by Git. Copy `.env.example` and set `OPENROUTER_API_KEY` only when intentionally making paid OpenRouter calls.

## Phase 1 — Fictional fables

Phase 1 is the synthetic baseline. Five unfamiliar worlds each contain two valid, ordered three-step procedures. The task asks for one procedure without naming the preferred path or the hypothesis. This lets the supplied document be effectively the model’s entire knowledge of the world.

The original exploratory six-condition, 600-call study is preserved unchanged at [`experiments/pilot-exploratory/`](experiments/pilot-exploratory/). It is historical only: it is not Experiment 0 and is never included in the chain runner.

The controlled replacement is the following nine-experiment chain:

| # | Directory | Question / independent variable |
|---:|---|---|
| 1 | `01-recommendation-presence` | Does adding an explicit recommendation change path selection? |
| 2 | `02-structural-isolation` | Same recommendation isolated in a paragraph vs enmeshed in prose. |
| 3 | `03-heading-effect` | Isolated recommendation with a heading vs without one. |
| 4 | `04-ai-audience-targeting` | `For AI agents and LLMs` vs `Recommended approach`; heading text only. |
| 5 | `05-html-vs-markdown` | Semantically equivalent raw HTML vs raw Markdown. |
| 6 | `06-semantic-compression` | Full human-oriented document vs proposition-preserving concise Markdown. |
| 7 | `07-stronger-compression` | Moderate compression vs a stronger ordinary-English compression. |
| 8 | `08-context-dilution` | Same task core in a short vs much longer irrelevant context. |
| 9 | `09-conflict-prior-correction` | Current recommendation isolated vs enmeshed after a historical alternative. |

Experiments 1–5 decompose the comparisons bundled into the exploratory pilot. Experiments 6–9 test how that behavior survives compression, context, and a plausible competing alternative. Each experiment is independently runnable; a null result in an earlier experiment does not skip a later one.

Every Phase 1 experiment has exactly two conditions, five worlds, frozen artifact hashes, and an experiment-specific validator. Default execution is 5 worlds × 2 conditions × 3 repetitions = **30 calls per experiment**; a nine-experiment chain is **270 calls/model**. Temperature-zero repetitions are low-variance repeated observations, not fully independent experimental units.

Useful commands:

```bash
python -m benchmark experiments list
python -m benchmark experiment 2 inspect
python -m benchmark experiment 2 diff
python -m benchmark experiment 2 validate
python -m benchmark experiment 1 run --model anthropic/claude-sonnet-4.6 --runs 3
python -m benchmark chain inspect --model anthropic/claude-sonnet-4.6 --runs 3
python -m benchmark chain run --model anthropic/claude-sonnet-4.6 --runs 3 --execute
python -m benchmark chain summary results/
```

The first substantive Phase 1 run is Experiment 1: before testing representation, test whether an explicit recommendation changes behavior at all.

## Phase 2 — Real open-source documentation candidates

Phase 2 reuses the Phase 1 independent variables with real documentation, where supplied material must compete with learned API examples, historical conventions, and prior expectations. It is deliberately gated by calibration: a candidate must leave enough headroom after ordinary official documentation before a full nine-experiment battery is justified.

### SQLAlchemy — completed negative selection result

[`phase-2-real-docs/projects/sqlalchemy/`](phase-2-real-docs/projects/sqlalchemy/) contains frozen SQLAlchemy 2.0.52 sources, five executable SQLite tasks, AST classifiers, artifacts, raw calibration/results, and reports. Sonnet 4.6 selected current patterns 80% of the time with no document; ordinary official documentation raised that to 100%. The candidate therefore had no remaining primary-metric headroom for the structural battery. It is retained as evidence, not discarded.

The planned real-document analogues use the same nine independent variables as Phase 1: recommendation presence, isolation, heading, AI targeting, representation, two compression contrasts, context dilution, and conflict correction. Their frozen experiment metadata live under [`phase-2-real-docs/experiments/`](phase-2-real-docs/experiments/); they are not a completed SQLAlchemy chain.

### OpenTelemetry — completed negative selection result

[`phase-2-real-docs/projects/opentelemetry/`](phase-2-real-docs/projects/opentelemetry/) contains frozen official specification/migration sources, 12 candidate historical/current conflicts, five behavioral tasks, 17 decision-level scoring rules, and prior/documentation calibration records. Its score is high resolution: a response may be partly current and partly historical across individual semantic-convention or configuration decisions.

Sonnet 4.6 was 90.2% current without documentation and reached 100% with ordinary official documentation. It also failed the headroom gate; no artificial ambiguity or post-result tuning was added. See [`selection-result.md`](phase-2-real-docs/projects/opentelemetry/selection-result.md).

Local inspection and validation:

```bash
python -m benchmark real-docs inspect sqlalchemy
python -m benchmark real-docs validate sqlalchemy
python -m benchmark real-docs inspect opentelemetry
python -m benchmark real-docs candidates opentelemetry
python -m benchmark real-docs validate opentelemetry
```

## Phase 3 — OpenTelemetry `For agents` intervention

[`phase-3-agent-section/`](phase-3-agent-section/) tests a practical two-condition intervention on five OpenTelemetry tasks and 29 deterministically scored decisions:

| Condition | Documentation |
|---|---|
| A | Frozen normal official-documentation bundle. |
| B | The same bundle plus a concise, source-supported `For agents` section. |

The directory contains source snapshots, decision and proposition manifests, normal and `For agents` artifacts, byte-level diffs, scoring fixtures, raw results, and reports. It also holds two separate follow-ups:

- `follow-ups/attention-check/`: a clearly marked non-production counterfactual instruction diagnostic; it is not a documentation-quality experiment.
- `follow-ups/label-authority/`: a small generic-operational-heading vs `For agents` heading comparison.

```bash
python -m benchmark agent-section inspect opentelemetry
python -m benchmark agent-section diff opentelemetry
python -m benchmark agent-section validate opentelemetry
python -m benchmark agent-section run opentelemetry --model anthropic/claude-sonnet-4.6 --smoke
```

## Phase 4 — Pinecone section-heading pilot

[`phase-4-pinecone-label/`](phase-4-pinecone-label/) is a narrow replication of the section/label question using a frozen [Pinecone Quickstart](https://docs.pinecone.io/guides/get-started/quickstart) snapshot. The task generates a small integrated-embedding setup/search function. Four API choices are deterministically classified: model-based index creation, record ingestion, text search, and text inputs.

The current three-condition design makes two clean contrasts:

| Condition | Manipulation |
|---|---|
| N | Shared current Quickstart body with no section heading. |
| G | The same body under `## Recommended quickstart`. |
| AI | The same body under `## For AI agents and LLMs`. |

The original generic-versus-AI two-condition run remains preserved separately. The newer N/G/AI run adds the no-section control and showed a ceiling: all 36 scored decisions were current across nine calls. This is evidence about this task/source/model combination, not a claim that headings never matter.

```bash
python -m benchmark pinecone-label validate
python -m benchmark pinecone-label diff
python -m benchmark pinecone-label run --model anthropic/claude-sonnet-4.6 --runs 3
```

## Scoring, validation, and results

No study uses an LLM judge. Phase 1 scoring recognizes preferred, alternative, mixed, invalid, and sequence-correct answers. The real-document phases use deterministic API/decision manifests; where relevant they separately record functional correctness and current-versus-legacy pattern selection.

Before paid execution, validators confirm that each condition changes only its stated independent variable: exact recommendation identity, heading-only changes, normalized HTML/Markdown equivalence, proposition parity under compression, or identical task core under context expansion. Results are written one invocation per JSONL row and retain raw output, hashes, usage, latency, cost when supplied, and deterministic scores. Reports add counts, percentages, by-world/by-task breakdowns, Wilson intervals, and Fisher tests where useful.

Run the suite locally:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m benchmark validate
```

Provider calls are never made by inspection, validation, reporting, or dry-run commands. They require an explicit run command and `OPENROUTER_API_KEY` in the environment or `.env`.
