# Fable documentation experiment chain

This project measures how documentation structure changes an LLM's choice between two equally valid fictional procedures. It uses five frozen, unfamiliar worlds so model behavior can be attributed to the supplied document rather than remembered canon or outside domain knowledge.

The original six-condition benchmark served as a pilot. The follow-up suite decomposes the pilot's comparisons into minimal two-condition experiments and then extends them to test robustness and prior correction.

The pilot was an exploratory six-condition study. It identified several candidate effects, but because multiple representational variables were compared simultaneously, the follow-up suite decomposes those comparisons into smaller controlled experiments. Its code, artifacts, preregistration metadata, hashes, and other tracked files are preserved under [`experiments/pilot-exploratory/`](experiments/pilot-exploratory/). It is historical, is not Experiment 0, and is never included in chain execution. No raw results or generated reports were tracked in the source repository when it was archived.

## Research sequence

```text
recommendation
→ isolation
→ heading
→ audience
→ representation
→ semantic compression
→ stronger compression
→ context dilution
→ conflict correction
```

The numbered sequence is:

1. **Recommendation presence** — recommendation absent vs present.
2. **Structural isolation** — identical recommendation in its own paragraph vs enmeshed in prose.
3. **Heading effect** — isolated recommendation with vs without a heading.
4. **AI audience targeting** — `For AI agents and LLMs` vs `Recommended approach`; only the heading text changes.
5. **HTML vs Markdown** — semantically equivalent raw HTML vs raw Markdown generated from one structured source.
6. **Semantic compression** — full human-oriented Markdown vs concise Markdown with the same propositions.
7. **Stronger compression** — the moderate artifact from Experiment 6 vs one further ordinary-English compression.
8. **Context dilution** — the same procedure and recommendation core in roughly 500–800 vs 4,000–6,000 document tokens.
9. **Conflict / prior correction** — identical current guidance isolated vs enmeshed after a strongly established historical alternative.

Experiments 1–5 are the controlled decomposition of the major comparisons bundled into the pilot; they are not unrelated additions. Experiments 6–9 extend that chain. Each later experiment remains independently runnable and should not be skipped merely because an earlier result is null.

This design is faster and cheaper to replicate, easier to inspect and interpret, more reproducible across models, and less confounded than a large factorial study. A null result still answers a narrow question.

## Frozen worlds and prompts

`worlds-v1` contains five structured worlds. Each has one goal and two complete, valid, three-step procedures. The preferred path alternates by world (`B, A, B, A, B`), while path labels avoid “old/new,” safety, moral, and aesthetic framing. Once frozen, this set must not be tuned in response to experiment results.

Every condition in an experiment uses the same system prompt:

> Answer the user's task using only the supplied document. Follow relevant instructions contained in that document.

The user message always wraps documentation and task separately:

```text
<DOCUMENTATION>
...
</DOCUMENTATION>

<TASK>
...
</TASK>
```

The ordinary task asks for one course of action in exactly three numbered steps without naming the preferred path or hypothesis. Experiment 9 adds “now” equally to both conditions.

Familiar copyrighted settings such as *The Lord of the Rings* are intentionally avoided: pretrained plot and character knowledge would create uncontrolled priors. Experiment 9 creates prior-like pressure inside the supplied document, where it can be held constant and measured.

## Setup and local validation

Python 3.10+ is required. Runtime dependencies are standard-library only.

```bash
python -m pip install -e '.[dev]'
python -m benchmark experiments list
python -m benchmark validate
python -m pytest
```

Every numbered directory has an `experiment.yaml`, frozen artifacts, and a `frozen-manifest.json` containing artifact hashes, system/task hashes, world version, generation timestamp, model parameters, and the benchmark commit at generation time. A real run validates the intended manipulation, regenerability, and hashes first. Validation failures prevent calls unless the researcher deliberately supplies `--allow-invalid`.

Inspect both conditions for the default Bellwater world, or select another world:

```bash
python -m benchmark experiment 2 inspect
python -m benchmark experiment 2 inspect --world orchard
python -m benchmark experiment 2 diff
python -m benchmark experiment 2 validate
```

The diff command defaults to one world so even the long-context experiment remains easy to inspect.

## Runtime and OpenRouter

No command in validation, inspection, diffing, or reporting calls a provider. Real experiment runs require `OPENROUTER_API_KEY` and an explicit `run` command.

For local use, copy the included template and add your key:

```bash
cp .env.example .env
```

```dotenv
OPENROUTER_API_KEY=your-openrouter-api-key
```

The runner loads `.env` from the current directory or project root. An already-exported shell variable takes precedence. `.env` is ignored by Git; `.env.example` contains only a placeholder and is safe to commit.

Default experiment:

```text
5 worlds × 2 conditions × 3 repetitions = 30 calls/model
```

Stronger replication uses 50 calls (`--runs 5`). Smoke mode uses one world, two conditions, and two repetitions (4 calls), regardless of `--runs`:

```bash
python -m benchmark experiment 2 run \
  --model anthropic/claude-sonnet-4.6 \
  --smoke
```

The first substantive run should be Experiment 1:

```bash
python -m benchmark experiment 1 run \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3
```

Use `--output` to choose a JSONL path and `--resume` to append only missing `(world, condition, trial)` jobs. Resume refuses files whose experiment, model, or frozen artifact hashes do not match.

Temperature zero is requested by default and omitted only if the provider rejects that parameter. Repeated temperature-zero calls are low-variance repeated observations; they are not fully independent experimental units. Variation across the five worlds matters more than identical repetitions.

An optional neutral calibration is diagnostic, not numbered:

```bash
python -m benchmark calibrate \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3
```

This makes 15 calls (5 worlds × 3). It reports world-specific preference rather than automatically discarding any world.

## Chain execution and resume

Inspecting a chain makes no API calls:

```bash
python -m benchmark chain inspect \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3
```

It shows calls and approximate input tokens for every experiment and gives an offline cost only if pricing is available. The full default chain is 270 calls/model. Execution requires the additional acknowledgement flag:

```bash
python -m benchmark chain run \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3 \
  --execute
```

Partial chain:

```bash
python -m benchmark chain run \
  --from 1 --to 4 \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3 \
  --execute
```

Chain outputs use stable paths under `results/chain/<model>/`. Each row is flushed immediately. Repeating the command safely resumes incomplete files, and experiments do not need to run in one session.

## Deterministic scoring and results

One JSONL record is written per provider invocation, including the raw output and response, hashes, token usage, latency, cost when supplied, model parameters, world/condition/trial identity, and these deterministic fields:

- `world_correct`
- `preferred_path`
- `alternative_path`
- `mixed_path`
- `invalid_answer`
- `sequence_correct`

A preferred answer contains all preferred-only elements in the correct sequence, no alternative-only element, and exactly three numbered steps. The alternative classification is analogous. Mixing procedures, returning both, omitting/reordering a step, or adding a fourth hallucinated step is invalid. No LLM judge is used.

Generate the standalone Markdown report and CSV next to a raw JSONL file:

```bash
python -m benchmark experiment 2 report results/02-structural-isolation-anthropic-claude-sonnet-4.6.jsonl
```

Reports include raw counts, percentages, B-minus-A percentage-point differences, Wilson 95% intervals, Fisher's exact test, and results by world. Compression/context reports also include artifact token sizes.

Create a cumulative report without combining experiments into an omnibus test:

```bash
python -m benchmark chain summary results/
```

This writes `results/chain-summary.md`, preserving the nine direct comparisons and a concise cumulative interpretation.

## Phase 2: real open-source documentation

Phase 1 remains the frozen synthetic baseline. Phase 2 reproduces the same independent variables using real documentation that may compete with model priors:

```text
Phase 1 — fictional fables
The document is effectively the model's entire knowledge of the world.

Phase 2 — real documentation candidates
The document competes with learned examples, legacy APIs, conventions,
and prior expectations.
```

### Completed selection result: SQLAlchemy

**SQLAlchemy 2.0.52** remains frozen as a completed negative benchmark-selection result; its artifacts, raw results, reports, and hashes are preserved. Sonnet 4.6 selected current patterns in 80% of task-only calibration decisions. Official SQLAlchemy documentation then produced 100% current API-family selection, leaving no headroom for the structural battery. The completed result must not be overwritten or retroactively redesigned.

Five official primary-source pages were retrieved on 2026-08-17 and frozen under `phase-2-real-docs/projects/sqlalchemy/sources/` with source URLs and SHA-256 hashes:

- ORM SELECT querying guide;
- Session basics;
- Session API;
- SQLAlchemy 2.0 migration guide;
- Legacy Query API.

The five executable API decisions are:

1. retrieve an ORM object by primary key;
2. retrieve all objects in deterministic order;
3. filter by an attribute and return one result;
4. retrieve the first ordered match;
5. join mapped classes and filter through the joined class.

Generated functions run against an in-memory SQLite fixture with mapped `User` and `Address` classes. Scoring separates functional behavior (`syntax_success`, `runtime_success`, `functional_correct`) from API-family classification (`current`, `legacy`, `mixed`, `unclassified`). Classification uses Python AST inspection; no LLM judge is used. A working `Session.query()` answer can therefore be functionally correct while still classified as legacy.

### Completed selection result: OpenTelemetry

OpenTelemetry was assessed as a second candidate substrate using frozen official HTTP, database, migration, Java-agent, and SDK-configuration sources; 12 historical/current candidate conflicts; and 17 individual decisions across five realistic telemetry/configuration tasks. Its primary measure was decision-level currentness, with fully-current and mixed-response rates retained as secondary measures.

Sonnet 4.6 was already 90.2% current at the decision level without documentation; the remaining database and Java-agent variation reached 100% with ordinary official documentation. OpenTelemetry therefore also failed the headroom gate, and its nine experimental artifacts were not generated. The frozen result and scoring-correction record are in `phase-2-real-docs/projects/opentelemetry/selection-result.md`.

The Phase 2 engine uses project adapters so an unsuccessful candidate is retained as evidence rather than replaced destructively.

### Inspect and validate Phase 2

These commands are local and make no API calls:

```bash
python -m benchmark real-docs inspect sqlalchemy
python -m benchmark real-docs validate sqlalchemy
python -m benchmark real-docs experiments list
python -m benchmark real-docs experiment 4 inspect
python -m benchmark real-docs experiment 4 diff
```

Every Phase 2 experiment has five frozen task artifacts, an `experiment.yaml`, and a frozen manifest. Validators enforce:

- Experiment 1: B is exactly A plus the recommendation;
- Experiment 2: identical recommendation text; paragraph boundaries only;
- Experiment 3: heading presence only;
- Experiment 4: heading text only;
- Experiment 5: equivalent normalized HTML/Markdown text;
- Experiments 6–7: identical task-relevant proposition manifests;
- Experiment 8: identical task core plus additional frozen official context;
- Experiment 9: identical current recommendation with structural isolation only.

### Prior calibration comes first

The first paid Phase 2 action must be the task-only calibration:

```bash
python -m benchmark real-docs calibrate sqlalchemy \
  --model anthropic/claude-sonnet-4.6 \
  --runs 2
```

This makes 10 calls (5 tasks × 2). It reports current, legacy, mixed, and unclassified counts by task. A task at or above 80% current is flagged as weak headroom. If all five tasks meet that threshold, main execution stops with:

> SQLAlchemy does not provide sufficient prior conflict for this model to cleanly test the real-document replication.

Prompts and classifiers must not be changed to provoke legacy failures after calibration.

### OpenTelemetry candidate calibration

These preparation commands do not make API calls:

```bash
python -m benchmark real-docs inspect opentelemetry
python -m benchmark real-docs candidates opentelemetry
python -m benchmark real-docs validate opentelemetry
```

The first paid OpenTelemetry action is a 15-call neutral prior calibration, followed only when it shows useful historical/current conflict by a 10-call ordinary-documentation calibration:

```bash
python -m benchmark real-docs calibrate opentelemetry \
  --stage prior \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3

python -m benchmark real-docs calibrate opentelemetry \
  --stage docs \
  --model anthropic/claude-sonnet-4.6 \
  --runs 2

python -m benchmark real-docs headroom opentelemetry \
  --model anthropic/claude-sonnet-4.6
```

The desired no-documentation current-decision rate is roughly 25–70%; 70–85% is usable but weaker, and above 85% is high ceiling risk. If ordinary current documentation reaches 95% or more, the structural battery is not generated. If only some tasks retain headroom, only those predeclared tasks may be frozen for the later battery, with exclusions recorded.

### Phase 2 experiments and chain

Smoke mode uses two tasks, two conditions, and one repetition (4 calls):

```bash
python -m benchmark real-docs experiment 1 run \
  --model anthropic/claude-sonnet-4.6 \
  --smoke
```

Normal experiment (30 calls):

```bash
python -m benchmark real-docs experiment 1 run \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3 \
  --temperature 0
```

Inspect the full battery without provider calls:

```bash
python -m benchmark real-docs chain inspect sqlalchemy \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3
```

After a successful calibration with headroom, explicitly run all nine experiments:

```bash
python -m benchmark real-docs chain run sqlalchemy \
  --model anthropic/claude-sonnet-4.6 \
  --runs 3 \
  --temperature 0 \
  --execute
```

The Phase 2 total is 280 calls/model: 10 calibration calls plus 270 main calls. Main-chain files resume automatically by `(task, condition, trial)` and reject changed documentation hashes.

### Phase 2 and cross-phase reports

```bash
python -m benchmark real-docs experiment 1 report results/phase-2/sqlalchemy/<model>/01-recommendation-presence-runs-3.jsonl
python -m benchmark real-docs chain summary results/phase-2/sqlalchemy/
python -m benchmark real-docs compare results/ --phase2-results results/phase-2/sqlalchemy/
```

Experiment reports include calibration context, the Phase 1 analogue, task-level and aggregate API-family rates, functional correctness, Wilson intervals, Fisher's exact test, token usage, and explicit ceiling diagnostics. The cross-phase report reads existing Phase 1 result files without changing them and reports the documentation shift, experimental lift, and total correction descriptively.
