# OpenTelemetry candidate substrate

This was a candidate replacement for the completed SQLAlchemy negative result. It stopped at two paid calibration gates: a no-documentation prior calibration and an official-documentation calibration. The nine experimental artifacts were deliberately not generated because ordinary documentation left no decision-level headroom.

The five proposed behavioral tasks contain 17 independently classified semantic decisions. The source of truth is the frozen official-source manifest and [decision manifests](scoring/decision-manifests.json), never an LLM judge.

OpenTelemetry is now a completed negative candidate-selection result. See [selection-result.md](selection-result.md).

Use:

```bash
python -m benchmark real-docs candidates opentelemetry
python -m benchmark real-docs validate opentelemetry
python -m benchmark real-docs calibrate opentelemetry --stage prior --model anthropic/claude-sonnet-4.6 --runs 3
python -m benchmark real-docs calibrate opentelemetry --stage docs --model anthropic/claude-sonnet-4.6 --runs 2
python -m benchmark real-docs headroom opentelemetry --model anthropic/claude-sonnet-4.6
```
