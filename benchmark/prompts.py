from .experiments import load_artifact, sha256_text
from .worlds import ROOT, load_world, task_for

SYSTEM_PROMPT = (ROOT / "fixtures" / "system.txt").read_text(encoding="utf-8").rstrip("\n")


def task(experiment, world_id):
    return task_for(load_world(world_id), experiment.id)


def documentation(experiment, world_id, condition):
    return load_artifact(experiment, world_id, condition)


def user_prompt(experiment, world_id, condition):
    return (
        f"<DOCUMENTATION>\n{documentation(experiment, world_id, condition)}</DOCUMENTATION>\n\n"
        f"<TASK>\n{task(experiment, world_id)}\n</TASK>"
    )
