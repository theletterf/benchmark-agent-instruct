import hashlib

from benchmark.real_docs.otel_reports import write_calibration_report, write_candidate_report, write_headroom_report
from benchmark.real_docs.otel_runner import assess_headroom, read_jsonl, run_calibration
from benchmark.real_docs.otel_scoring import score_response
from benchmark.real_docs.projects import opentelemetry as project


def _mapping(task, mode="current"):
    values = []
    for decision in task.decisions:
        value = decision.current[0] if mode == "current" else decision.historical[0]
        values.append(value if ":" in value else f"{value}: value")
    return "\n".join(values)


def test_frozen_opentelemetry_sources_and_candidate_mappings():
    assert project.validate_sources() == []
    assert 8 <= len(project.candidates()) <= 12
    assert len(project.tasks()) == 5
    assert sum(len(task.decisions) for task in project.tasks()) == 17
    for source in project.source_manifest()["sources"]:
        path = project.SOURCES / source["snapshot"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]
    known = {source["id"] for source in project.source_manifest()["sources"]}
    for task in project.tasks():
        for decision in task.decisions:
            assert decision.source_id in known and decision.current and decision.historical


def test_current_historical_mixed_and_invalid_decision_scoring():
    task = project.get_task("database-client-span")
    current = score_response(task, _mapping(task, "current"))
    assert current.current_decisions == 5 and current.fully_current and not current.mixed_response
    historical = score_response(task, _mapping(task, "historical"))
    assert historical.historical_decisions == 5 and not historical.fully_current
    mixed = score_response(task, "db.system.name: postgresql\ndb.statement: SELECT 1\ndb.namespace: shop\ndb.operation.name: SELECT\ndb.collection.name: orders")
    assert mixed.mixed_response and mixed.current_decisions == 4 and mixed.historical_decisions == 1
    invalid = score_response(task, "instrument: database\nquery: SELECT 1")
    assert invalid.current_decisions == 0 and all(item.classification == "unclassified" for item in invalid.decisions)


def test_prefix_historical_names_do_not_make_current_output_mixed():
    task = project.get_task("database-client-span")
    result = score_response(task, _mapping(task, "current"))
    assert all(item.classification == "current" for item in result.decisions)


def test_yaml_answer_is_scored_without_historical_explanatory_prose():
    task = project.get_task("java-agent-configuration")
    response = """```yaml
exporter_protocol: http/protobuf
effective_service_name: checkout
```

The older default was grpc."""
    result = score_response(task, response)
    assert result.fully_current and not result.mixed_response


def test_equivalent_nested_yaml_service_name_is_current():
    task = project.get_task("java-agent-configuration")
    result = score_response(task, "exporter:\n  protocol: http/protobuf\nservice:\n  name: checkout")
    assert result.fully_current


def _fake_completion(model, system, user, api_key, temperature=0.0):
    task = next(task for task in project.tasks() if task.prompt in user)
    raw = _mapping(task, "current")
    return {"choices": [{"message": {"content": raw}}], "model": model, "usage": {"prompt_tokens": 20, "completion_tokens": 20, "cost": 0}, "_latency_ms": 1}


def test_two_stage_calibration_reports_and_headroom(tmp_path, monkeypatch):
    prior = tmp_path / "prior.jsonl"
    docs = tmp_path / "docs.jsonl"
    run_calibration("fixture/model", "prior", 1, prior, completion_fn=_fake_completion)
    run_calibration("fixture/model", "docs", 1, docs, completion_fn=_fake_completion)
    prior_rows, docs_rows = read_jsonl(prior), read_jsonl(docs)
    assert len(prior_rows) == len(docs_rows) == 5
    assert all(row["documentation_sha256"] is None for row in prior_rows)
    assert all(row["documentation_sha256"] for row in docs_rows)
    assessment = assess_headroom(prior_rows, docs_rows)
    assert assessment["docs_current_decision_rate"] == 1.0 and not assessment["suitable"]
    _, prior_report = write_calibration_report(prior_rows, prior)
    assert "Decision-level currentness" in prior_report.read_text()
    candidate_report = write_candidate_report(tmp_path / "candidates.md")
    assert "http-method" in candidate_report.read_text()
