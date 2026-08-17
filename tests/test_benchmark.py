import json
from pathlib import Path

import pytest

from benchmark.chain import inspect_chain
from benchmark.env import load_dotenv
from benchmark.evaluator import score
from benchmark.experiments import (
    EXPERIMENTS,
    approx_tokens,
    artifact_metadata,
    artifact_path,
    get_experiment,
    list_experiments,
    load_artifact,
    normalize_html_text,
    normalize_markdown_text,
    render_artifact,
    unified_diff,
    validate_all,
    validate_experiment,
)
from benchmark.reports import read_jsonl, write_chain_summary, write_experiment_reports
from benchmark.runner import run_experiment
from benchmark.worlds import WORLD_VERSION, all_worlds, load_world, preferred_path, proposition_manifest, world_ids


def numbered(lines):
    return "\n".join(f"{index}. {line}" for index, line in enumerate(lines, 1))


def path_output(path):
    return numbered([step["text"] for step in path["steps"]])


def test_experiment_discovery_and_order():
    assert [(experiment.id, experiment.name) for experiment in list_experiments()] == [
        (1, "recommendation-presence"), (2, "structural-isolation"), (3, "heading-effect"),
        (4, "ai-audience-targeting"), (5, "html-vs-markdown"), (6, "semantic-compression"),
        (7, "stronger-compression"), (8, "context-dilution"), (9, "conflict-prior-correction"),
    ]
    assert get_experiment("02-structural-isolation").id == 2
    assert all((experiment.directory / "experiment.yaml").exists() for experiment in EXPERIMENTS)


def test_worlds_v1_is_frozen_balanced_and_has_three_step_paths():
    worlds = all_worlds()
    assert WORLD_VERSION == "worlds-v1" and len(worlds) == 5
    assert [world["preferred_path"] for world in worlds] == ["path_b", "path_a", "path_b", "path_a", "path_b"]
    for world in worlds:
        assert len(world["path_a"]["steps"]) == len(world["path_b"]["steps"]) == 3
        assert "old" not in world["path_a"]["label"] and "new" not in world["path_b"]["label"]


def test_dotenv_loads_key_without_overriding_exported_value(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("# local credentials\nOPENROUTER_API_KEY='from-dotenv'\nEXTRA_SETTING=value # comment\n")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("EXTRA_SETTING", raising=False)
    path, loaded = load_dotenv(env_file)
    assert path == env_file
    assert loaded == {"OPENROUTER_API_KEY", "EXTRA_SETTING"}
    assert __import__("os").environ["OPENROUTER_API_KEY"] == "from-dotenv"
    assert __import__("os").environ["EXTRA_SETTING"] == "value"

    monkeypatch.setenv("OPENROUTER_API_KEY", "already-exported")
    _, loaded = load_dotenv(env_file)
    assert "OPENROUTER_API_KEY" not in loaded
    assert __import__("os").environ["OPENROUTER_API_KEY"] == "already-exported"


def test_frozen_artifacts_equal_structured_generation_and_hashes():
    for experiment in EXPERIMENTS:
        manifest = json.loads((experiment.directory / "frozen-manifest.json").read_text())
        for world in all_worlds():
            for condition in ("A", "B"):
                actual = load_artifact(experiment, world["id"], condition)
                assert actual == render_artifact(experiment.id, world, condition).rstrip() + "\n"
                assert artifact_metadata(experiment, world["id"], condition)["sha256"] == manifest["artifacts"][world["id"]][condition]["sha256"]


def test_every_experiment_specific_validator_passes():
    statuses = validate_all()
    assert statuses == {experiment.id: [] for experiment in EXPERIMENTS}


def test_condition_diffs_show_only_intended_examples():
    diff2 = unified_diff(2, "bellwater")
    assert "The civic calendar" in diff2 and "When advising a traveler" in diff2
    assert "## Recommended approach" not in diff2
    diff4 = unified_diff(4, "bellwater")
    changed = [line for line in diff4.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    assert changed == ["-## For AI agents and LLMs", "+## Recommended approach"]
    diff5 = unified_diff(5, "bellwater")
    assert "-<h1>Entering Bellwater</h1>" in diff5 and "+# Entering Bellwater" in diff5


def test_semantic_compression_proposition_parity_and_sizes():
    for experiment_id in (6, 7):
        experiment = get_experiment(experiment_id)
        manifest = json.loads((experiment.directory / "frozen-manifest.json").read_text())
        for world in all_worlds():
            assert manifest["proposition_manifests"][world["id"]] == proposition_manifest(world)
            assert artifact_metadata(experiment, world["id"], "B")["approx_tokens"] < artifact_metadata(experiment, world["id"], "A")["approx_tokens"]
    for world in all_worlds():
        assert 500 <= len(load_artifact(get_experiment(6), world["id"], "A").split()) <= 900


def test_html_markdown_text_equivalence():
    experiment = get_experiment(5)
    for world in world_ids():
        assert normalize_html_text(load_artifact(experiment, world, "A")) == normalize_markdown_text(load_artifact(experiment, world, "B"))


def test_context_lengths_and_recommendation_position_are_controlled():
    experiment = get_experiment(8)
    for world in world_ids():
        short = artifact_metadata(experiment, world, "A")
        long = artifact_metadata(experiment, world, "B")
        assert 500 <= short["approx_tokens"] <= 800
        assert 4000 <= long["approx_tokens"] <= 6000
        assert abs(short["recommendation_position_fraction"] - long["recommendation_position_fraction"]) < 0.08


def test_deterministic_scoring_hand_written_fixtures():
    world = load_world("bellwater")
    preferred = preferred_path(world)
    alternative = world["path_a"]
    clean_preferred = path_output(preferred)
    clean_alternative = path_output(alternative)
    mixed = numbered([preferred["steps"][0]["text"], alternative["steps"][1]["text"], preferred["steps"][2]["text"]])
    both = clean_preferred + "\n" + clean_alternative
    missing = numbered([preferred["steps"][0]["text"], preferred["steps"][1]["text"], "Stop and wait."])
    wrong_order = numbered([preferred["steps"][2]["text"], preferred["steps"][1]["text"], preferred["steps"][0]["text"]])
    hallucinated = clean_preferred + "\n4. Ring a silver bell."

    assert score(world, clean_preferred).preferred_path
    assert score(world, clean_alternative).alternative_path
    assert score(world, mixed).mixed_path and score(world, mixed).invalid_answer
    assert score(world, both).invalid_answer and not score(world, both).world_correct
    assert score(world, missing).invalid_answer and not score(world, missing).sequence_correct
    assert score(world, wrong_order).invalid_answer and not score(world, wrong_order).sequence_correct
    assert score(world, hallucinated).invalid_answer and not score(world, hallucinated).world_correct


def fake_completion(model, system, user, api_key, temperature=0.0):
    assert "<DOCUMENTATION>" in user and "<TASK>" in user
    raw = "1. Cross the reed bridge at dawn.\n2. Give rosemary to the miller.\n3. Enter through the blue gate."
    return {
        "choices": [{"message": {"content": raw}}], "model": model,
        "usage": {"prompt_tokens": 123, "completion_tokens": 24, "cost": 0.0},
        "_latency_ms": 1.25, "_temperature_sent": temperature,
    }


def test_jsonl_persistence_and_interrupted_resume(tmp_path):
    output = tmp_path / "run.jsonl"
    run_experiment(1, "fixture/model", ["bellwater"], 2, output, seed=4, completion_fn=fake_completion)
    rows = read_jsonl(output)
    assert len(rows) == 4 and all("raw_output" in row for row in rows)
    assert {row["trial"] for row in rows} == {1, 2}

    output.write_text(json.dumps(rows[0]) + "\n", encoding="utf-8")
    run_experiment(1, "fixture/model", ["bellwater"], 2, output, seed=4, resume=True, completion_fn=fake_completion)
    resumed = read_jsonl(output)
    assert len(resumed) == 4
    assert len({(row["world"], row["condition"], row["trial"]) for row in resumed}) == 4


def test_individual_report_csv_and_markdown(tmp_path):
    output = tmp_path / "exp1.jsonl"
    run_experiment(1, "fixture/model", ["bellwater"], 2, output, completion_fn=fake_completion)
    csv_path, md_path = write_experiment_reports(read_jsonl(output), output, 1)
    report = md_path.read_text()
    assert csv_path.exists() and "# Experiment 1 — Recommendation presence" in report
    assert "Wilson 95%" in report and "By world" in report and "Fisher's exact" in report


def test_chain_inspection_and_summary(tmp_path):
    items = inspect_chain("fixture/model", runs=3)
    assert len(items) == 9 and all(item.calls == 30 for item in items)
    assert sum(item.calls for item in items) == 270

    result_dir = tmp_path / "results"
    output = result_dir / "exp1.jsonl"
    run_experiment(1, "fixture/model", ["bellwater"], 1, output, completion_fn=fake_completion)
    summary = write_chain_summary(result_dir)
    text = summary.read_text()
    assert "# Documentation experiment chain" in text
    assert "| 1 | Recommendation presence" in text
    assert "| 9 | Conflict / prior correction | — | — | — |" in text


def test_pilot_snapshot_keeps_original_preregistration_hashes():
    pilot = Path("experiments/pilot-exploratory")
    prereg = json.loads((pilot / "fixtures/preregistration.json").read_text())
    artifact = pilot / "worlds/bellwater/A.md"
    import hashlib
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == prereg["worlds"]["bellwater"]["artifacts"]["A"]["sha256"]
    assert (pilot / "benchmark/runner.py").exists()
