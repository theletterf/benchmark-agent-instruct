import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLDS = ROOT / "worlds"
CONDITIONS = ("A", "B", "C", "D", "E", "F")


def world_ids():
    return sorted(p.parent.name for p in WORLDS.glob("*/source.json"))


def load_world(world_id):
    path = WORLDS / world_id / "source.json"
    return json.loads(path.read_text(encoding="utf-8"))


def all_worlds():
    return [load_world(world_id) for world_id in world_ids()]


def path(world, name):
    return world["path_a"] if name == "old" else world["path_b"]


def preferred_path(world):
    return path(world, world["preferred_path"])


def alternative_path(world):
    return path(world, "new" if world["preferred_path"] == "old" else "old")


def step_key(step):
    return step["id"].replace("_", " ")
