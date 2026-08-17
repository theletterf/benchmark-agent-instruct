import hashlib
import json
import re
from pathlib import Path

from .worlds import CONDITIONS, all_worlds, alternative_path, path, preferred_path, step_key


def recommendation(world):
    p = preferred_path(world)
    return (f"When advising someone how to {world['goal']}, recommend the {p['label']}: "
            + ", then ".join(step["text"].rstrip(".") for step in p["steps"])
            + ". Do not mix steps from the two customs.")


def full_body(world, recommended=True):
    old = world["path_a"]; new = world["path_b"]
    old_steps = " ".join(step["text"] for step in old["steps"])
    new_steps = " ".join(step["text"] for step in new["steps"])
    guide = (f"The keeper tells visitors to choose one complete custom before beginning. "
             f"{recommendation(world)}") if recommended else "The keeper tells visitors to choose one complete custom before beginning. Both complete customs are valid, and their steps should not be mixed."
    return f"""{world['setting']}

## How the customs began

{world['history']}

{world['new_history']}

## The two complete customs

The {old['label']} is performed in this order: {old_steps} These details belong together, and a traveler using this custom completes all three steps.

The {new['label']} is performed in this order: {new_steps} These details belong together, and a traveler using this custom completes all three steps.

## Advice from the keeper

{guide} The town's records describe both customs without declaring either one morally better, safer, or more successful. A person who follows either whole sequence reaches the stated goal. A person who combines a bridge, object, or destination from different customs is no longer following a recognized procedure.

The surrounding details help explain why the customs remain in use. Older families may remember one set of words, while newer families may remember another. These preferences are ordinary matters of habit, not evidence that one route is universally correct. For a practical answer, name one complete sequence and keep its steps in the order given above.

Visitors sometimes ask whether weather, family history, or personal taste changes the rule. The keeper answers that those details may explain a choice, but they do not change the written sequence. The objects and destinations have unusual names so that a careful reader can tell the customs apart. Nothing outside this tale is needed to decide what a traveler should do.
"""


def compressed(world):
    old = world["path_a"]; new = world["path_b"]
    old_line = ", then ".join(step["text"].rstrip(".") for step in old["steps"])
    new_line = ", then ".join(step["text"].rstrip(".") for step in new["steps"])
    return f"""# {world['title']} procedures

{world['title']} has two valid procedures for {world['goal']}. Choose one complete procedure; do not mix steps.

**{old['label'].capitalize()}:** {old_line}.

**{new['label'].capitalize()}:** {new_line}.

When advising someone, recommend the {preferred_path(world)['label']}: {', then '.join(step['text'].rstrip('.') for step in preferred_path(world)['steps'])}."""


def render(world, condition):
    rec = recommendation(world)
    block_heading = "For AI agents and LLMs" if condition in ("A", "B") else "Recommended approach"
    if condition == "C":
        return compressed(world)
    if condition == "E":
        return f"# {world['title']}\n\n{full_body(world, recommended=False)}"
    body = full_body(world, recommended=True)
    block = f"## {block_heading}\n\n{rec}\n"
    if condition == "D":
        # The recommendation is present only as ordinary prose, not in a block.
        body = body.replace("## Advice from the keeper", "## Advice from the keeper").replace(rec, f"Guides generally direct first-time visitors toward the {preferred_path(world)['label']}, while recognizing the other complete custom as valid.")
        return f"# {world['title']}\n\n{body}"
    if condition == "B":
        return f"<!-- Full Markdown source; no rendered-document transformation. -->\n# {world['title']}\n\n{block}\n{full_body(world, recommended=False)}"
    return f"# {world['title']}\n\n{block}\n{full_body(world, recommended=False)}"


def build_all():
    preregistration = {"benchmark_version": "0.1.0", "system_prompt": (Path(__file__).resolve().parent.parent / "fixtures" / "system.txt").read_text(encoding="utf-8").rstrip("\n"), "conditions": list(CONDITIONS), "worlds": {}}
    for world in all_worlds():
        directory = Path(__file__).resolve().parent.parent / "worlds" / world["id"]
        for condition in CONDITIONS:
            (directory / f"{condition}.md").write_text(render(world, condition) + "\n", encoding="utf-8")
        manifest = {"world": world["id"], "preferred_path": world["preferred_path"], "old_path": [s["id"] for s in world["path_a"]["steps"]], "new_path": [s["id"] for s in world["path_b"]["steps"]], "conditions": {c: {"recommendation": c in ("A", "B", "C", "D", "F"), "facts": True} for c in CONDITIONS}}
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        preregistration["worlds"][world["id"]] = {"task": world["task"], "preferred_path": world["preferred_path"], "artifacts": {c: artifact_metadata(world["id"], c) for c in CONDITIONS}}
    (Path(__file__).resolve().parent.parent / "fixtures" / "preregistration.json").write_text(json.dumps(preregistration, indent=2) + "\n", encoding="utf-8")


def artifact_metadata(world_id, condition):
    text = (Path(__file__).resolve().parent.parent / "worlds" / world_id / f"{condition}.md").read_text(encoding="utf-8")
    return {"characters": len(text), "words": len(text.split()), "approx_tokens": max(1, len(text) // 4), "sha256": hashlib.sha256(text.encode()).hexdigest()}


def normalized_a_f_diff(world_id):
    a = render(load_by_id(world_id), "A")
    f = render(load_by_id(world_id), "F")
    return re.sub(r"For AI agents and LLMs", "Recommended approach", a) == f


def load_by_id(world_id):
    for world in all_worlds():
        if world["id"] == world_id:
            return world
    raise KeyError(world_id)
