import hashlib
from pathlib import Path

from .worlds import ROOT, load_world

SYSTEM_PROMPT = (ROOT / "fixtures" / "system.txt").read_text(encoding="utf-8").rstrip("\n")


def task(world_id):
    return load_world(world_id)["task"]


def documentation(world_id, condition):
    return (ROOT / "worlds" / world_id / f"{condition}.md").read_text(encoding="utf-8")


def user_prompt(world_id, condition):
    return f"<DOCUMENTATION>\n{documentation(world_id, condition)}</DOCUMENTATION>\n\n<TASK>\n{task(world_id)}\n</TASK>"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
