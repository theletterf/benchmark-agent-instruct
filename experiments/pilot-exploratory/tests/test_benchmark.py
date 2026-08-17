import json
from pathlib import Path

from benchmark.artifacts import CONDITIONS, build_all, normalized_a_f_diff
from benchmark.evaluator import score
from benchmark.prompts import documentation
from benchmark.reports import write_reports
from benchmark.worlds import all_worlds

PREFERRED = """1. Cross the reed bridge at dawn.
2. Give the miller a sprig of rosemary.
3. Enter through the blue gate."""
ALTERNATIVE = """1. Cross the stone bridge at dusk.
2. Give the gatekeeper a copper coin.
3. Enter through the oak gate."""
MIXED = """1. Cross the reed bridge.
2. Give the gatekeeper a copper coin.
3. Enter through the blue gate."""
BOTH = PREFERRED + "\n" + ALTERNATIVE
HALLUCINATED = "1. Cross the marble bridge.\n2. Ring a silver bell.\n3. Enter the red gate."


def bellwater():
    return next(w for w in all_worlds() if w["id"] == "bellwater")


def test_all_worlds_and_artifacts_validate():
    build_all()
    worlds = all_worlds()
    assert len(worlds) == 5
    for world in worlds:
        assert len(world["path_a"]["steps"]) == 3
        assert len(world["path_b"]["steps"]) == 3
        assert all(len(documentation(world["id"], c)) > 100 for c in CONDITIONS)
        assert normalized_a_f_diff(world["id"])


def test_deterministic_path_scoring():
    result = score(bellwater(), PREFERRED)
    assert result.world_correct and result.preferred_path and not result.alternative_path
    result = score(bellwater(), ALTERNATIVE)
    assert result.world_correct and result.alternative_path and not result.preferred_path
    result = score(bellwater(), MIXED)
    assert result.mixed_path and result.invalid_answer and not result.world_correct
    result = score(bellwater(), BOTH)
    assert result.invalid_answer and not result.world_correct
    result = score(bellwater(), HALLUCINATED)
    assert result.invalid_answer and not result.world_correct


def test_sequence_order_is_required():
    result = score(bellwater(), "blue gate, rosemary, reed bridge")
    assert not result.world_correct and result.invalid_answer


def test_reports(tmp_path):
    row = {"model":"fixture", "world":"bellwater", "condition":"A", "world_correct":True, "preferred_path":True,
           "alternative_path":False, "mixed_path":False, "invalid_answer":False, "prompt_tokens":10,
           "completion_tokens":5, "latency_ms":2, "cost_usd":0.1}
    path = tmp_path / "results.jsonl"; path.write_text(json.dumps(row) + "\n")
    csv_path, md_path = write_reports([row], path)
    assert csv_path.exists() and md_path.exists() and "bellwater" in md_path.read_text()


def test_fixtures_are_versioned_sources():
    assert (Path("fixtures") / "experiment.json").exists()
    assert "AI agents" not in (Path("fixtures") / "system.txt").read_text()


def test_condition_boundaries():
    for world in all_worlds():
        d = documentation(world["id"], "D").lower()
        e = documentation(world["id"], "E").lower()
        c = documentation(world["id"], "C")
        assert "ai agents" not in d and "llms" not in d
        assert "recommend" not in e
        assert "→" not in c and ">" not in c
