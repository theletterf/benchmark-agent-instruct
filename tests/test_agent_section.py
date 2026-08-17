import json
from pathlib import Path

from benchmark.agent_section.artifacts import (
    BLOCK_END,
    BLOCK_START,
    remove_agent_block,
    token_metrics,
    validate_all,
    validate_propositions,
)
from benchmark.agent_section.attention_check import attention_score, attention_artifact, build as build_attention_check, strip_attention_check, validate as validate_attention_check
from benchmark.agent_section.project import (
    MANIFEST_ROOT,
    PHASE_ROOT,
    artifact_path,
    decisions,
    tasks,
    validate_source_hashes,
)
from benchmark.agent_section.reports import render_report, write_report
from benchmark.agent_section.runner import plan, read_jsonl, run_experiment, serialize_result
from benchmark.agent_section.scoring import score_response


FIXTURES = PHASE_ROOT / "scoring" / "fixtures"


def test_frozen_sources_tasks_and_decision_manifests():
    assert validate_source_hashes() == []
    assert [task.id for task in tasks()] == [
        "http-client-telemetry", "http-server-telemetry", "http-client-duration",
        "database-client-telemetry", "java-agent-configuration",
    ]
    assert sum(len(decisions(task.id)) for task in tasks()) == 29
    assert (MANIFEST_ROOT / "frozen-artifacts.json").is_file()


def test_ab_identity_and_source_support_validation():
    assert validate_all() == []
    for task in tasks():
        normal = artifact_path(task.id, "A").read_text(encoding="utf-8")
        treatment = artifact_path(task.id, "B").read_text(encoding="utf-8")
        assert treatment.count(BLOCK_START) == treatment.count(BLOCK_END) == 1
        assert remove_agent_block(treatment).encode() == normal.encode()
        assert validate_propositions(task.id) == []


def test_handwritten_current_historical_mixed_and_invalid_fixtures():
    current = score_response("http-client-telemetry", (FIXTURES / "fully-current.json").read_text())
    partly_historical = score_response("http-client-telemetry", (FIXTURES / "partly-historical.json").read_text())
    historical = score_response("http-client-telemetry", (FIXTURES / "fully-historical.json").read_text())
    mixed = score_response("http-client-telemetry", (FIXTURES / "mixed.json").read_text())
    invalid = score_response("http-client-telemetry", (FIXTURES / "invalid.txt").read_text())
    assert current.fully_correct and current.current_correct_decisions == 6
    assert partly_historical.historical_decisions == 1 and partly_historical.mixed_current_historical
    assert historical.current_correct_decisions == 1 and historical.historical_decisions == 5
    assert mixed.mixed_decisions == 1 and mixed.mixed_current_historical
    assert invalid.invalid_decisions == 6 and not invalid.fully_correct


def test_token_counts_are_positive_and_treatment_costs_more():
    for task in tasks():
        counts = token_metrics(task.id)
        assert counts["normal_documentation_tokens"] > 0
        assert counts["agent_section_tokens"] > 0
        assert counts["treatment_tokens"] > counts["normal_documentation_tokens"]
        assert counts["percentage_context_increase"] > 0


def test_separate_attention_check_is_byte_additive_and_scores_counterfactuals():
    build_attention_check()
    assert validate_attention_check() == []
    base = artifact_path("http-client-telemetry", "B").read_text(encoding="utf-8")
    assert strip_attention_check(attention_artifact("http-client-telemetry")).encode() == base.encode()
    response = json.dumps({"span_kind": "CLIENT", "attributes": {"http.method": "POST", "http.status_code": 201, "http.url": "https://shop.example:8443/orders/42?view=full", "net.peer.name": "shop.example", "net.peer.port": 8443}})
    score = attention_score("http-client-telemetry", response)
    assert score["attention_check_followed"] == score["attention_check_decisions"] == 5


def _fake_completion(model, system, user, api_key, temperature=0.0):
    assert system == "Use the supplied documentation to complete the task."
    assert "<DOCUMENTATION>" in user and "<TASK>" in user
    if "HTTP client sends POST" in user:
        raw = (FIXTURES / "fully-current.json").read_text()
    elif "HTTPS server" in user:
        raw = json.dumps({"span_kind": "SERVER", "attributes": {"http.request.method": "GET", "http.response.status_code": 200, "url.path": "/orders/42", "url.scheme": "https", "http.route": "/orders/{orderId}", "server.address": "api.example"}})
    else:
        raise AssertionError("unexpected smoke task")
    return {"choices": [{"message": {"content": raw}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}, "model": model, "_latency_ms": 1.0, "_temperature_sent": temperature}


def test_smoke_plan_result_serialization_and_report(tmp_path):
    assert len(plan(smoke=True, runs=999, seed=7)) == 4
    assert len(plan(smoke=False, runs=3, seed=7)) == 30
    output = tmp_path / "smoke.jsonl"
    run_experiment("fixture/model", smoke=True, output=output, completion_fn=_fake_completion)
    rows = read_jsonl(output)
    assert len(rows) == 4 and {row["condition"] for row in rows} == {"A", "B"}
    assert all(row["fully_correct"] for row in rows)
    repaired = tmp_path / "one.jsonl"
    serialize_result(repaired, rows[0])
    assert read_jsonl(repaired) == [rows[0]]
    report = write_report(output)
    text = report.read_text(encoding="utf-8")
    assert "# Phase 3 — For agents intervention" in text and "## Token overhead" in text
    assert "Decision-level difference" in render_report(rows, "fixture")
