from __future__ import annotations

import difflib
import hashlib
import html
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from .worlds import ROOT, WORLD_VERSION, all_worlds, load_world, preferred_path, proposition_manifest, task_for

EXPERIMENTS_ROOT = ROOT / "experiments"
CONDITIONS = ("A", "B")


@dataclass(frozen=True)
class Experiment:
    id: int
    name: str
    title: str
    research_question: str
    independent_variable: str
    condition_a: str
    condition_b: str
    primary_metric: str = "preferred_path"
    secondary_metrics: tuple[str, ...] = (
        "world_correct", "alternative_path", "mixed_path", "invalid_answer", "sequence_correct"
    )
    default_runs: int = 3

    @property
    def directory(self):
        return EXPERIMENTS_ROOT / f"{self.id:02d}-{self.name}"

    def condition_label(self, condition):
        return self.condition_a if condition == "A" else self.condition_b


EXPERIMENTS = (
    Experiment(1, "recommendation-presence", "Recommendation presence", "Does adding an explicit recommendation change which valid procedure is selected?", "recommendation presence", "neutral", "recommendation present"),
    Experiment(2, "structural-isolation", "Structural isolation", "Does isolating otherwise identical recommendation wording increase preferred-path compliance?", "paragraph isolation", "isolated paragraph", "enmeshed prose"),
    Experiment(3, "heading-effect", "Heading effect", "Once a recommendation is isolated, does adding a heading make it more influential?", "heading presence", "heading", "no heading"),
    Experiment(4, "ai-audience-targeting", "AI audience targeting", "Does explicitly addressing AI agents and LLMs give an instruction additional weight?", "audience label", "AI-targeted heading", "generic heading"),
    Experiment(5, "html-vs-markdown", "HTML vs Markdown", "Does raw document representation affect compliance when textual content is equivalent?", "raw markup representation", "HTML", "Markdown"),
    Experiment(6, "semantic-compression", "Semantic compression", "Can human-oriented narrative be removed without reducing behavioral compliance?", "semantic compression", "full document", "semantically compressed document"),
    Experiment(7, "stronger-compression", "Stronger compression", "How much further can semantic compression go before behavior changes?", "compression strength", "moderate compression", "strong compression"),
    Experiment(8, "context-dilution", "Context dilution", "Does an isolated recommendation retain its influence in much more irrelevant context?", "irrelevant context length", "short context", "long context"),
    Experiment(9, "conflict-prior-correction", "Conflict / prior correction", "Does structural isolation help current guidance override a strongly established historical alternative?", "current recommendation isolation", "isolated current recommendation", "enmeshed current recommendation"),
)


def list_experiments():
    return list(EXPERIMENTS)


def get_experiment(value):
    text = str(value).strip().lower()
    for experiment in EXPERIMENTS:
        if text in {str(experiment.id), experiment.name, f"{experiment.id:02d}-{experiment.name}"}:
            return experiment
    raise KeyError(f"unknown experiment: {value}")


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def approx_tokens(text):
    return max(1, (len(text) + 3) // 4)


def _steps_sentence(path):
    pieces = [step["text"].rstrip(".") for step in path["steps"]]
    pieces = [piece[:1].lower() + piece[1:] for piece in pieces]
    return f"first, {pieces[0]}; next, {pieces[1]}; finally, {pieces[2]}"


def recommendation(world, separate_constraint=True, current=False):
    lead = "When advising a traveler today" if current else "When advising a traveler"
    preferred = preferred_path(world)
    text = f"{lead}, recommend the {preferred['label']}: {_steps_sentence(preferred)}."
    separator = "\n\n" if separate_constraint else " "
    qualifier = "the current procedure with the historical custom" if current else "this procedure with the other custom"
    return f"{text}{separator}Do not mix {qualifier}."


def procedure_paragraphs(world):
    a, b = world["path_a"], world["path_b"]
    return [
        f"The {a['label']} is one complete valid procedure. In order: " + " ".join(step["text"] for step in a["steps"]),
        f"The {b['label']} is one complete valid procedure. In order: " + " ".join(step["text"] for step in b["steps"]),
        "Both procedures remain valid. Choose one complete procedure and keep its three steps together and in order.",
    ]


def neutral_document(world):
    blocks = [f"# {world['title']}", f"{world['place'].capitalize()} recognizes two valid procedures for someone who needs to {world['goal']}."]
    blocks.extend(procedure_paragraphs(world))
    return "\n\n".join(blocks)


def recommended_block(world, heading="Recommended approach", current=False):
    return f"## {heading}\n\n{recommendation(world, separate_constraint=True, current=current)}"


def _background_paragraph(world, index):
    topic = world["context_topics"][index % len(world["context_topics"])]
    cycle = index // len(world["context_topics"]) + 1
    return (
        f"The local notes on {topic} are arranged in cycle {cycle} by season and district. Clerks record dates, materials, attendance, and routine maintenance so residents can compare one year with another. "
        "These records explain ordinary civic administration rather than travel customs. Entries are reviewed at public meetings, copied into bound volumes, and stored by calendar year. "
        "The wording stays descriptive: it identifies who maintained each record, where the work occurred, and when the next review is due. Nothing in this material changes either recognized procedure."
    )


def _full_document(world):
    sections = [f"# {world['title']}", "## Local background"]
    sections.extend(_background_paragraph(world, index) for index in range(6))
    sections.extend(["## The two valid procedures", *procedure_paragraphs(world), recommended_block(world)])
    sections.extend([
        "## Why the record is detailed",
        "The archive keeps explanatory material for human readers who may be unfamiliar with local terminology. It repeats the purpose of the record, distinguishes description from advice, and gives enough setting for the procedures to be understood without outside sources. The added narrative does not create a third procedure and does not change the order of any required action.",
    ])
    return "\n\n".join(sections)


def _moderately_compressed(world):
    a, b = world["path_a"], world["path_b"]
    return "\n\n".join([
        f"# {world['title']}",
        f"Two complete procedures are valid for someone who needs to {world['goal']}. Use every step from one procedure, in order, without combining procedures.",
        f"**{a['label'].capitalize()}:** " + " ".join(step["text"] for step in a["steps"]),
        f"**{b['label'].capitalize()}:** " + " ".join(step["text"] for step in b["steps"]),
        recommended_block(world),
    ])


def _strongly_compressed(world):
    a, b, preferred = world["path_a"], world["path_b"], preferred_path(world)
    return "\n\n".join([
        f"# {world['title']}",
        f"Two complete procedures are valid for {world['goal']}:",
        f"- **{a['label'].capitalize()}:** " + " ".join(step["text"] for step in a["steps"]),
        f"- **{b['label'].capitalize()}:** " + " ".join(step["text"] for step in b["steps"]),
        "## Recommended approach",
        f"Recommend the {preferred['label']}. Follow its three steps above in order; do not mix procedures.",
    ])


def _representation_blocks(world):
    return [
        ("h1", world["title"]),
        ("p", f"{world['place'].capitalize()} recognizes two valid procedures for someone who needs to {world['goal']}."),
        ("p", procedure_paragraphs(world)[0]),
        ("p", procedure_paragraphs(world)[1]),
        ("p", procedure_paragraphs(world)[2]),
        ("h2", "Recommended approach"),
        ("p", recommendation(world).split("\n\n")[0]),
        ("p", recommendation(world).split("\n\n")[1]),
    ]


def _render_html(world):
    output = []
    in_section = False
    for kind, text in _representation_blocks(world):
        if kind == "h2":
            output.extend(["<section>", f"  <h2>{html.escape(text)}</h2>"])
            in_section = True
        elif in_section:
            output.append(f"  <p>{html.escape(text)}</p>")
        else:
            output.append(f"<{kind}>{html.escape(text)}</{kind}>")
    if in_section:
        output.append("</section>")
    return "\n\n".join(output)


def _render_markdown(world):
    rendered = []
    for kind, text in _representation_blocks(world):
        prefix = "# " if kind == "h1" else "## " if kind == "h2" else ""
        rendered.append(prefix + text)
    return "\n\n".join(rendered)


def _context_document(world, long=False):
    pre_indexes = range(20) if long else range(2)
    post_indexes = range(20, 40) if long else range(20, 22)
    core = "\n\n".join(["## The two valid procedures", *procedure_paragraphs(world), recommended_block(world)])
    return "\n\n".join([
        f"# {world['title']}", "## Regional background",
        *(_background_paragraph(world, index) for index in pre_indexes),
        core,
        "## Administrative notes",
        *(_background_paragraph(world, index) for index in post_indexes),
    ])


def _conflict_document(world, isolated):
    historical = world["path_b" if world["preferred_path"] == "path_a" else "path_a"]
    sequence = " ".join(step["text"] for step in historical["steps"])
    common = "\n\n".join([
        f"# {world['title']}",
        "## Historical practice",
        f"For generations, most people used the {historical['label']}. The historical record gives this sequence: {sequence}",
        f"Old registers mention the {historical['label']} repeatedly because it was once the usual choice. They again record the same sequence: {sequence}",
        "Both the historical procedure and the other procedure remain factually possible. The registry distinguishes historical practice from current guidance.",
    ])
    rec = recommendation(world, separate_constraint=False, current=True)
    tail = "The archive retains the historical notes so readers can understand the change over time."
    if isolated:
        return f"{common}\n\n## Current recommended approach\n\n{rec}\n\n{tail}"
    return f"{common} {rec} {tail}"


def render_artifact(experiment_id, world, condition):
    experiment_id = int(experiment_id)
    if condition not in CONDITIONS:
        raise KeyError(condition)
    if experiment_id == 1:
        base = neutral_document(world)
        return base if condition == "A" else f"{base}\n\n{recommended_block(world)}"
    if experiment_id == 2:
        base = neutral_document(world)
        before = "The civic calendar is reviewed every sixth day."
        after = "The northern record room closes during winter."
        rec = recommendation(world, separate_constraint=False)
        addition = f"{before}\n\n{rec}\n\n{after}" if condition == "A" else f"{before} {rec} {after}"
        return f"{base}\n\n{addition}"
    if experiment_id == 3:
        base = neutral_document(world)
        rec = recommendation(world)
        addition = f"## Recommended approach\n\n{rec}" if condition == "A" else rec
        return f"{base}\n\n{addition}"
    if experiment_id == 4:
        heading = "For AI agents and LLMs" if condition == "A" else "Recommended approach"
        return f"{neutral_document(world)}\n\n{recommended_block(world, heading)}"
    if experiment_id == 5:
        return _render_html(world) if condition == "A" else _render_markdown(world)
    if experiment_id == 6:
        return _full_document(world) if condition == "A" else _moderately_compressed(world)
    if experiment_id == 7:
        return _moderately_compressed(world) if condition == "A" else _strongly_compressed(world)
    if experiment_id == 8:
        return _context_document(world, long=condition == "B")
    if experiment_id == 9:
        return _conflict_document(world, isolated=condition == "A")
    raise KeyError(experiment_id)


def artifact_path(experiment, world_id, condition):
    suffix = ".html" if experiment.id == 5 and condition == "A" else ".md"
    return experiment.directory / "artifacts" / world_id / f"{condition}{suffix}"


def load_artifact(experiment, world_id, condition):
    return artifact_path(experiment, world_id, condition).read_text(encoding="utf-8")


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def normalize_html_text(text):
    parser = _TextExtractor()
    parser.feed(text)
    return " ".join(" ".join(parser.parts).split())


def normalize_markdown_text(text):
    text = re.sub(r"(?m)^#{1,6}\s+", "", text)
    text = re.sub(r"[*_`]", "", text)
    return " ".join(text.split())


def _normalized_ws(text):
    return " ".join(text.split())


def _assert_propositions(world, text):
    lowered = text.lower()
    for path_name in ("path_a", "path_b"):
        positions = [lowered.find(step["key"].lower()) for step in world[path_name]["steps"]]
        if any(position < 0 for position in positions):
            raise ValueError(f"{world['id']}: missing {path_name} proposition")
        if positions != sorted(positions):
            raise ValueError(f"{world['id']}: {path_name} propositions are out of order")
    if preferred_path(world)["label"].lower() not in lowered and _steps_sentence(preferred_path(world)).lower() not in lowered:
        raise ValueError(f"{world['id']}: preferred recommendation is absent")
    if "do not mix" not in lowered and "without combining" not in lowered:
        raise ValueError(f"{world['id']}: no-mixing proposition is absent")
    return proposition_manifest(world)


def _validate_manipulation(experiment, world, a, b):
    rec_joined = recommendation(world, separate_constraint=False)
    if experiment.id == 1:
        expected = f"{a.rstrip()}\n\n{recommended_block(world)}"
        if b.rstrip() != expected:
            raise ValueError("recommended condition differs beyond the added recommendation block")
    elif experiment.id == 2:
        if a.count(rec_joined) != 1 or b.count(rec_joined) != 1 or _normalized_ws(a) != _normalized_ws(b):
            raise ValueError("recommendation wording or non-boundary text differs")
    elif experiment.id == 3:
        if a.replace("## Recommended approach\n\n", "", 1) != b:
            raise ValueError("conditions differ beyond heading presence")
    elif experiment.id == 4:
        if "AI agents" in b or "LLMs" in b:
            raise ValueError("AI wording occurs outside the AI-targeted condition")
        if a.replace("For AI agents and LLMs", "Recommended approach", 1) != b:
            raise ValueError("conditions differ beyond heading text")
    elif experiment.id == 5:
        if normalize_html_text(a) != normalize_markdown_text(b):
            raise ValueError("HTML and Markdown normalized text is not equivalent")
    elif experiment.id in (6, 7):
        if _assert_propositions(world, a) != _assert_propositions(world, b):
            raise ValueError("task-relevant proposition manifests differ")
    elif experiment.id == 8:
        core = "\n\n".join(["## The two valid procedures", *procedure_paragraphs(world), recommended_block(world)])
        if a.count(core) != 1 or b.count(core) != 1:
            raise ValueError("procedure or recommendation core differs")
        if approx_tokens(a) not in range(500, 801):
            raise ValueError(f"short context is {approx_tokens(a)} tokens; expected 500–800")
        if approx_tokens(b) not in range(4000, 6001):
            raise ValueError(f"long context is {approx_tokens(b)} tokens; expected 4000–6000")
        extra = b.replace(core, "").lower()
        for path_name in ("path_a", "path_b"):
            for step in world[path_name]["steps"]:
                if step["key"].lower() in extra:
                    raise ValueError("long-context filler mentions a scoring entity")
        if "recommend" in extra:
            raise ValueError("long-context filler contains recommendation language")
    elif experiment.id == 9:
        rec = recommendation(world, separate_constraint=False, current=True)
        if a.count(rec) != 1 or b.count(rec) != 1:
            raise ValueError("current recommendation wording is not identical")
        normalized_a = _normalized_ws(a.replace("## Current recommended approach", "", 1))
        if normalized_a != _normalized_ws(b):
            raise ValueError("conditions differ beyond current-guidance isolation")


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def freeze_all(generation_timestamp=None):
    generated = generation_timestamp or datetime.now(timezone.utc).isoformat()
    system = (ROOT / "fixtures" / "system.txt").read_text(encoding="utf-8").rstrip("\n")
    commit = git_commit()
    worlds_source = ROOT / "worlds-v1" / "worlds.json"
    world_manifest = {
        "world_version": WORLD_VERSION,
        "frozen": True,
        "generation_timestamp": generated,
        "benchmark_commit": commit,
        "source_sha256": sha256_text(worlds_source.read_text(encoding="utf-8")),
        "worlds": {
            world["id"]: {
                "preferred_path": world["preferred_path"],
                "task_sha256": sha256_text(task_for(world)),
                "propositions": proposition_manifest(world),
            }
            for world in all_worlds()
        },
    }
    (ROOT / "worlds-v1" / "frozen-manifest.json").write_text(json.dumps(world_manifest, indent=2) + "\n", encoding="utf-8")
    for experiment in EXPERIMENTS:
        artifacts = {}
        for world in all_worlds():
            artifacts[world["id"]] = {}
            for condition in CONDITIONS:
                text = render_artifact(experiment.id, world, condition).rstrip() + "\n"
                path = artifact_path(experiment, world["id"], condition)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                artifacts[world["id"]][condition] = {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": sha256_text(text),
                    "characters": len(text),
                    "words": len(text.split()),
                    "approx_tokens": approx_tokens(text),
                }
        manifest = {
            "experiment": experiment.id,
            "experiment_name": experiment.name,
            "world_version": WORLD_VERSION,
            "generation_timestamp": generated,
            "benchmark_commit": commit,
            "system_prompt_sha256": sha256_text(system),
            "task_sha256": {world["id"]: sha256_text(task_for(world, experiment.id)) for world in all_worlds()},
            "model_parameters": {"temperature": 0.0},
            "artifacts": artifacts,
            "proposition_manifests": {world["id"]: proposition_manifest(world) for world in all_worlds()} if experiment.id in (6, 7) else None,
        }
        (experiment.directory / "frozen-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_experiment(value):
    experiment = get_experiment(value)
    errors = []
    worlds_source = ROOT / "worlds-v1" / "worlds.json"
    worlds_manifest_path = ROOT / "worlds-v1" / "frozen-manifest.json"
    if not worlds_manifest_path.exists():
        errors.append("missing worlds-v1/frozen-manifest.json")
    else:
        worlds_manifest = json.loads(worlds_manifest_path.read_text(encoding="utf-8"))
        if worlds_manifest.get("source_sha256") != sha256_text(worlds_source.read_text(encoding="utf-8")):
            errors.append("worlds-v1 source differs from its frozen hash")
    yaml_path = experiment.directory / "experiment.yaml"
    if not yaml_path.exists():
        errors.append("missing experiment.yaml")
    else:
        yaml = yaml_path.read_text(encoding="utf-8")
        if not re.search(rf"(?m)^id:\s*{experiment.id}\s*$", yaml) or not re.search(rf"(?m)^name:\s*{re.escape(experiment.name)}\s*$", yaml):
            errors.append("experiment.yaml id/name do not match registry")
    manifest_path = experiment.directory / "frozen-manifest.json"
    if not manifest_path.exists():
        errors.append("missing frozen-manifest.json")
        return errors
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    system = (ROOT / "fixtures" / "system.txt").read_text(encoding="utf-8").rstrip("\n")
    if manifest.get("system_prompt_sha256") != sha256_text(system):
        errors.append("system prompt hash differs from frozen manifest")
    for world in all_worlds():
        try:
            texts = {}
            for condition in CONDITIONS:
                actual = load_artifact(experiment, world["id"], condition)
                expected = render_artifact(experiment.id, world, condition).rstrip() + "\n"
                texts[condition] = actual.rstrip()
                if actual != expected:
                    raise ValueError(f"{condition} artifact differs from structured renderer")
                recorded = manifest["artifacts"][world["id"]][condition]["sha256"]
                if sha256_text(actual) != recorded:
                    raise ValueError(f"{condition} artifact hash differs from frozen manifest")
            if manifest["task_sha256"][world["id"]] != sha256_text(task_for(world, experiment.id)):
                raise ValueError("task hash differs from frozen manifest")
            _validate_manipulation(experiment, world, texts["A"], texts["B"])
        except (KeyError, OSError, ValueError) as exc:
            errors.append(f"{world['id']}: {exc}")
    return errors


def validate_all():
    return {experiment.id: validate_experiment(experiment.id) for experiment in EXPERIMENTS}


def artifact_metadata(experiment, world_id, condition):
    text = load_artifact(experiment, world_id, condition)
    metadata = {
        "characters": len(text), "words": len(text.split()), "approx_tokens": approx_tokens(text), "sha256": sha256_text(text)
    }
    rec = "## Recommended approach"
    start = text.find(rec)
    if start >= 0:
        metadata["recommendation_start_token"] = approx_tokens(text[:start])
        metadata["recommendation_position_fraction"] = round(start / len(text), 4)
    return metadata


def unified_diff(value, world_id=None):
    experiment = get_experiment(value)
    ids = [world_id] if world_id else [world["id"] for world in all_worlds()]
    chunks = []
    for current in ids:
        a, b = load_artifact(experiment, current, "A"), load_artifact(experiment, current, "B")
        chunks.extend(difflib.unified_diff(a.splitlines(), b.splitlines(), fromfile=f"{current}/A", tofile=f"{current}/B", lineterm=""))
    return "\n".join(chunks) + ("\n" if chunks else "")


def experiment_as_dict(experiment):
    data = asdict(experiment)
    data["directory"] = str(experiment.directory.relative_to(ROOT))
    return data
