import hashlib
import json
from pathlib import Path

from benchmark.real_docs.artifacts import (
    EXPERIMENTS,
    artifact_metadata,
    get_experiment,
    load_artifact,
    normalized_html,
    normalized_markdown,
    validate_all,
)
from benchmark.real_docs.chain import inspect_chain
from benchmark.real_docs.classifier import classify_code, extract_code
from benchmark.real_docs.fixture import evaluate_output
from benchmark.real_docs.projects import sqlalchemy as project
from benchmark.real_docs.reports import (
    write_calibration_report,
    write_cross_phase_report,
    write_experiment_report,
    write_phase2_summary,
)
from benchmark.real_docs.runner import assess_headroom, read_jsonl, run_calibration, run_experiment


def test_frozen_sqlalchemy_sources_and_hashes():
    manifest = project.source_manifest()
    assert manifest["documentation_version"] == manifest["runtime_version"] == "2.0.52"
    assert project.validate_sources() == []
    for source in manifest["sources"]:
        path = project.SOURCES / source["snapshot"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]


def test_five_tasks_and_machine_readable_manifests():
    assert project.task_ids() == ["primary-key-lookup", "retrieve-all", "filter-one", "first-matching", "join-filter"]
    for task in project.tasks():
        manifest = project.PROJECT_ROOT / "tasks" / task.id / "scoring-manifest.json"
        payload = json.loads(manifest.read_text())
        assert payload["current_patterns"] and payload["legacy_patterns"] and payload["required_behavior"]


def test_current_and_legacy_references_are_functionally_equivalent():
    for task in project.tasks():
        current = evaluate_output(task, task.current_reference)
        legacy = evaluate_output(task, task.legacy_reference)
        assert current.syntax_success and current.runtime_success and current.functional_correct
        assert legacy.syntax_success and legacy.runtime_success and legacy.functional_correct
        assert current.api_classification == "current"
        assert legacy.api_classification == "legacy"


def test_manual_mixed_invalid_and_functionally_wrong_fixtures():
    task = project.get_task("primary-key-lookup")
    mixed_code = """def find_user_by_id(session, user_id):
    if user_id == 999:
        return session.query(User).get(user_id)
    return session.get(User, user_id)
"""
    mixed = evaluate_output(task, mixed_code)
    assert mixed.api_classification == "mixed" and mixed.mixed and mixed.functional_correct

    invalid = evaluate_output(task, "def find_user_by_id(session, user_id)\n    return None")
    assert not invalid.syntax_success and not invalid.runtime_success and invalid.api_classification == "unclassified"

    wrong = evaluate_output(task, "def find_user_by_id(session, user_id):\n    return session.get(User, 999)")
    assert wrong.api_classification == "current" and wrong.runtime_success and not wrong.functional_correct

    unclassified = evaluate_output(task, "def find_user_by_id(session, user_id):\n    return None")
    assert unclassified.api_classification == "unclassified" and unclassified.runtime_success and not unclassified.functional_correct


def test_code_extraction_and_ast_detection():
    task = project.get_task("retrieve-all")
    output = "Explanation.\n```python\n" + task.current_reference + "\n```\nMore text."
    code = extract_code(output, task.function_name)
    classification, current, legacy, calls, mixed = classify_code(task, code)
    assert code == task.current_reference
    assert classification == "current" and current > 0 and legacy == 0 and not mixed
    assert any(call.endswith("scalars") for call in calls)

    primary = project.get_task("primary-key-lookup")
    alternate_current = "def find_user_by_id(session, user_id):\n    return session.scalars(select(User).where(User.id == user_id)).one_or_none()"
    assert evaluate_output(primary, alternate_current).api_classification == "current"
    assert evaluate_output(primary, alternate_current).functional_correct


def test_all_phase2_manipulation_validators_and_frozen_hashes():
    assert validate_all() == {experiment.id: [] for experiment in EXPERIMENTS}
    for experiment in EXPERIMENTS:
        manifest = json.loads((Path("phase-2-real-docs/experiments") / f"{experiment.id:02d}-{experiment.name}" / "frozen-manifest.json").read_text())
        for task in project.tasks():
            for condition in ("A", "B"):
                assert artifact_metadata(experiment, task.id, condition)["sha256"] == manifest["artifacts"][task.id][condition]["sha256"]


def test_html_markdown_equivalence_compression_and_context():
    for task in project.tasks():
        assert normalized_html(load_artifact(get_experiment(5), task.id, "A")) == normalized_markdown(load_artifact(get_experiment(5), task.id, "B"))
        full = artifact_metadata(get_experiment(6), task.id, "A")["approx_tokens"]
        moderate = artifact_metadata(get_experiment(6), task.id, "B")["approx_tokens"]
        strong = artifact_metadata(get_experiment(7), task.id, "B")["approx_tokens"]
        assert full > moderate > strong
        assert 25 <= 100 * (moderate - strong) / moderate <= 45
        focused = artifact_metadata(get_experiment(8), task.id, "A")
        broad = artifact_metadata(get_experiment(8), task.id, "B")
        assert broad["approx_tokens"] in range(4000, 6001) and broad["approx_tokens"] > focused["approx_tokens"]


def fake_completion(model, system, user, api_key, temperature=0.0):
    task = next(task for task in project.tasks() if task.signature in user)
    raw = "```python\n" + task.current_reference + "\n```"
    return {"choices": [{"message": {"content": raw}}], "model": model,
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0},
            "_latency_ms": 1.0, "_temperature_sent": temperature}


def test_calibration_persistence_headroom_and_report(tmp_path):
    output = tmp_path / "calibration.jsonl"
    run_calibration("fixture/model", 2, output, completion_fn=fake_completion)
    rows = read_jsonl(output)
    assert len(rows) == 10 and all(row["documentation_sha256"] is None for row in rows)
    assessment = assess_headroom(rows)
    assert assessment["insufficient_headroom"] and all(item["weak_headroom"] for item in assessment["tasks"])
    csv_path, md_path = write_calibration_report(rows, output)
    assert csv_path.exists() and "not Experiment 0" in md_path.read_text()


def test_jsonl_persistence_resume_and_experiment_report(tmp_path):
    output = tmp_path / "experiment.jsonl"
    run_experiment(1, "fixture/model", project.task_ids()[:2], 1, output, completion_fn=fake_completion)
    rows = read_jsonl(output)
    assert len(rows) == 4 and all(row["functional_correct"] and row["api_classification"] == "current" for row in rows)
    output.write_text(json.dumps(rows[0]) + "\n")
    run_experiment(1, "fixture/model", project.task_ids()[:2], 1, output, resume=True, completion_fn=fake_completion)
    resumed = read_jsonl(output)
    assert len(resumed) == 4 and len({(row["task"], row["condition_code"], row["trial"]) for row in resumed}) == 4
    csv_path, md_path = write_experiment_report(resumed, output, 1)
    report = md_path.read_text()
    assert csv_path.exists() and "Functional correctness" in report and "No detectable difference under a ceiling condition" in report


def test_phase2_chain_call_counts_and_summaries(tmp_path):
    items = inspect_chain("fixture/model", 3)
    assert len(items) == 9 and all(item.calls == 30 for item in items) and sum(item.calls for item in items) == 270

    phase2_dir = tmp_path / "phase2"
    output = phase2_dir / "exp1.jsonl"
    run_experiment(1, "fixture/model", project.task_ids()[:2], 1, output, completion_fn=fake_completion)
    summary = write_phase2_summary(phase2_dir)
    assert "Phase 2 — Real documentation" in summary.read_text()

    phase1_dir = tmp_path / "phase1"
    phase1_dir.mkdir()
    phase1_rows = [
        {"experiment": 1, "model": "fixture/model", "condition": "A", "preferred_path": False},
        {"experiment": 1, "model": "fixture/model", "condition": "B", "preferred_path": True},
    ]
    (phase1_dir / "phase1.jsonl").write_text("\n".join(json.dumps(row) for row in phase1_rows) + "\n")
    comparison = write_cross_phase_report(phase1_dir, phase2_dir, tmp_path / "comparison.md")
    text = comparison.read_text()
    assert "Phase 1 vs Phase 2" in text and "Recommendation presence" in text
