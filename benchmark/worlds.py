import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLDS_FILE = ROOT / "worlds-v1" / "worlds.json"
WORLD_VERSION = "worlds-v1"


def _payload():
    payload = json.loads(WORLDS_FILE.read_text(encoding="utf-8"))
    if payload.get("version") != WORLD_VERSION or payload.get("frozen") is not True:
        raise ValueError("worlds-v1 must be explicitly versioned and frozen")
    return payload


def all_worlds():
    return _payload()["worlds"]


def world_ids():
    return [world["id"] for world in all_worlds()]


def load_world(world_id):
    for world in all_worlds():
        if world["id"] == world_id:
            return world
    raise KeyError(f"unknown world: {world_id}")


def preferred_path(world):
    return world[world["preferred_path"]]


def alternative_path(world):
    name = "path_b" if world["preferred_path"] == "path_a" else "path_a"
    return world[name]


def step_key(step):
    return step.get("key", step["id"].replace("_", " ")).lower()


def task_for(world, experiment_id=None):
    when = " now" if experiment_id == 9 else ""
    return (
        f"Based only on the supplied document, tell {world['character']} what to do{when}. "
        "Give one course of action in exactly three numbered steps."
    )


def proposition_manifest(world):
    return {
        "paths": {
            "path_a": [step["key"] for step in world["path_a"]["steps"]],
            "path_b": [step["key"] for step in world["path_b"]["steps"]],
        },
        "recommendation": {
            "preferred": world["preferred_path"],
            "do_not_mix": True,
        },
    }
