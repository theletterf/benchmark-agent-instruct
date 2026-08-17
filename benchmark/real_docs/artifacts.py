from __future__ import annotations

import difflib
import hashlib
import html
import json
import re
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from .models import RealExperiment
from .projects import sqlalchemy as project
from ..prompts import SYSTEM_PROMPT
from ..worlds import ROOT

PHASE_ROOT = ROOT / "phase-2-real-docs"
EXPERIMENTS_ROOT = PHASE_ROOT / "experiments"
CONDITIONS = ("A", "B")

EXPERIMENTS = (
    RealExperiment(1, "recommendation-presence", "Recommendation presence", "Does adding an explicit recommendation increase current-pattern selection over official documentation alone?", "recommendation presence", "official documentation", "official documentation plus recommendation"),
    RealExperiment(2, "structural-isolation", "Structural isolation", "Does an isolated current recommendation outperform identical wording embedded in prose?", "paragraph isolation", "isolated paragraph", "enmeshed prose"),
    RealExperiment(3, "heading-effect", "Heading effect", "Once a recommendation is isolated, does adding a heading change current-pattern selection?", "heading presence", "heading", "no heading"),
    RealExperiment(4, "ai-audience-targeting", "AI audience targeting", "Does explicitly addressing the model provide benefit in real documentation?", "audience label", "AI-targeted heading", "generic heading"),
    RealExperiment(5, "html-vs-markdown", "HTML vs Markdown", "Does raw representation affect current-pattern selection when semantic content is equivalent?", "raw markup representation", "HTML", "Markdown"),
    RealExperiment(6, "semantic-compression", "Semantic compression", "Can human-oriented documentation be compressed while preserving current-pattern steering?", "semantic compression", "full documentation", "semantically compressed Markdown"),
    RealExperiment(7, "stronger-compression", "Stronger compression", "Can the compressed representation be reduced further without losing corrective effect?", "compression strength", "moderate compression", "strong compression"),
    RealExperiment(8, "context-dilution", "Context dilution", "Does the recommendation remain effective with substantially more official context?", "official context breadth", "focused retrieval", "broad retrieval"),
    RealExperiment(9, "conflict-prior-correction", "Conflict / prior correction", "Does structural isolation help current guidance overcome salient official legacy information?", "current-correction isolation", "isolated current correction", "enmeshed current correction"),
)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def approx_tokens(text):
    return max(1, (len(text) + 3) // 4)


def get_experiment(value):
    key = str(value).lower().strip()
    for experiment in EXPERIMENTS:
        if key in {str(experiment.id), experiment.name, f"{experiment.id:02d}-{experiment.name}"}:
            return experiment
    raise KeyError(value)


def experiment_directory(experiment):
    return EXPERIMENTS_ROOT / f"{experiment.id:02d}-{experiment.name}"


def recommendation_block(task, heading="Recommended approach"):
    return f"## {heading}\n\n{task.recommendation}"


def official_document(task):
    return f"# {task.title}\n\n{task.official_excerpt}"


def _moderate_document(task):
    behavior = "\n".join(f"- {item}" for item in task.behavior)
    return f"""# {task.title}

SQLAlchemy 2.x uses the current ORM query family identified below. The older `Session.query()` family remains available as a legacy API, so working legacy code is not the same as current documented code.

## Required behavior

{behavior}

## Current API

{task.recommendation}

Use the stated result operation so the function preserves the required missing-result and ordering semantics. Do not combine the current `select()` / `Session` family with a legacy `Query` construction."""


def _strong_document(task):
    behavior = "\n".join(f"- {item}" for item in task.behavior)
    return f"""# {task.title}

## Required behavior

{behavior}

## Current API

{task.recommendation}

`Session.query()` is legacy. Do not mix it with the current API family. Preserve the listed result semantics and stated current operation."""


def _full_document(task):
    behavior = "\n".join(f"- {item}" for item in task.behavior)
    return f"""# {task.title}

## SQLAlchemy 2.0 ORM usage

{project.COMMON_QUERYING}

## Relevant official documentation

{task.official_excerpt}

## Application behavior

The benchmark fixture asks for a small function and supplies the mapped classes, session, and deterministic data. The implementation must satisfy all of these result semantics:

{behavior}

The distinction between functional behavior and API family matters: legacy `Query` code may still execute successfully even though it does not use the current documented family.

{recommendation_block(task)}"""


def _representation_blocks(task):
    return [
        ("h1", task.title),
        ("p", "Official SQLAlchemy 2.x documentation excerpt."),
        ("pre", task.official_excerpt),
        ("h2", "Recommended approach"),
        ("p", task.recommendation),
    ]


def _render_html(task):
    parts = []
    for kind, text in _representation_blocks(task):
        if kind == "pre":
            parts.append(f"<pre>{html.escape(normalized_markdown(text))}</pre>")
        else:
            parts.append(f"<{kind}>{html.escape(text)}</{kind}>")
    return "\n\n".join(parts)


def _render_markdown(task):
    parts = []
    for kind, text in _representation_blocks(task):
        prefix = "# " if kind == "h1" else "## " if kind == "h2" else ""
        parts.append(prefix + text)
    return "\n\n".join(parts)


def _broad_context():
    text = project.source_text("orm-querying-guide")
    start = text.find("SELECT statements are produced by the select() function")
    if start < 0:
        raise ValueError("could not locate broad-context anchor in frozen querying guide")
    # A literal flattened slice of the frozen official page, not generated filler.
    segment = text[start:start + 19000]
    midpoint = len(segment) // 2
    split = segment.rfind(". ", 0, midpoint) + 1
    return segment[:split].strip(), segment[split:].strip()


def _focused_core(task):
    return f"{official_document(task)}\n\n{recommendation_block(task)}"


def _conflict_document(task, isolated):
    common = f"""# {task.title}

## SQLAlchemy 1.x and 2.x ORM forms

{project.COMMON_QUERYING}

{task.official_excerpt}

The application behavior in the task can be implemented by code from either family because the legacy Query API remains available. The following application guidance identifies the current documented family."""
    tail = "The legacy examples remain in the record for migration and classification purposes."
    if isolated:
        return f"{common}\n\n## Current recommended approach\n\n{task.recommendation}\n\n{tail}"
    return f"{common} {task.recommendation} {tail}"


def render_artifact(experiment_id, task, condition):
    experiment_id = int(experiment_id)
    if condition not in CONDITIONS:
        raise KeyError(condition)
    base = official_document(task)
    if experiment_id == 1:
        return base if condition == "A" else f"{base}\n\n{recommendation_block(task)}"
    if experiment_id == 2:
        before = "The following application guidance applies to the function in the task."
        after = "The function must retain the result semantics stated in the task."
        addition = f"{before}\n\n{task.recommendation}\n\n{after}" if condition == "A" else f"{before} {task.recommendation} {after}"
        return f"{base}\n\n{addition}"
    if experiment_id == 3:
        addition = recommendation_block(task) if condition == "A" else task.recommendation
        return f"{base}\n\n{addition}"
    if experiment_id == 4:
        heading = "For AI agents and LLMs" if condition == "A" else "Recommended approach"
        return f"{base}\n\n{recommendation_block(task, heading)}"
    if experiment_id == 5:
        return _render_html(task) if condition == "A" else _render_markdown(task)
    if experiment_id == 6:
        return _full_document(task) if condition == "A" else _moderate_document(task)
    if experiment_id == 7:
        return _moderate_document(task) if condition == "A" else _strong_document(task)
    if experiment_id == 8:
        core = _focused_core(task)
        if condition == "A":
            return core
        before, after = _broad_context()
        return f"# Broader official SQLAlchemy querying context\n\n{before}\n\n{core}\n\n{after}"
    if experiment_id == 9:
        return _conflict_document(task, isolated=condition == "A")
    raise KeyError(experiment_id)


def artifact_path(experiment, task_id, condition):
    suffix = ".html" if experiment.id == 5 and condition == "A" else ".md"
    return project.PROJECT_ROOT / "artifacts" / f"{experiment.id:02d}-{experiment.name}" / task_id / f"{condition}{suffix}"


def load_artifact(experiment, task_id, condition):
    return artifact_path(experiment, task_id, condition).read_text(encoding="utf-8")


class _MarkupText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data.strip():
            self.parts.append(data.strip())


def normalized_html(text):
    parser = _MarkupText()
    parser.feed(text)
    return normalized_markdown(" ".join(parser.parts))


def normalized_markdown(text):
    text = re.sub(r"(?m)^#{1,6}\s+", "", text)
    text = re.sub(r"```(?:python)?|```|[*`]", "", text)
    return " ".join(text.split())


def _normalized_ws(text):
    return " ".join(text.split())


def _validate_official_excerpt(task):
    excerpt = normalized_markdown(task.official_excerpt)
    combined_sources = " ".join(project.source_text(source_id) for source_id in task.source_ids)
    errors = []
    for assertion in task.source_assertions:
        if assertion.lower() not in excerpt.lower():
            errors.append(f"official excerpt omits source assertion: {assertion}")
        if assertion.lower() not in combined_sources.lower():
            errors.append(f"frozen sources omit source assertion: {assertion}")
    return errors


def _validate_propositions(task, text):
    lowered = normalized_markdown(text).lower()
    if normalized_markdown(task.recommendation).lower() not in lowered:
        raise ValueError("current recommendation proposition is missing or changed")
    for behavior in task.behavior:
        if behavior.lower() not in lowered:
            raise ValueError(f"required behavior proposition missing: {behavior}")
    if "legacy" not in lowered:
        raise ValueError("legacy/current distinction is missing")
    return project.proposition_manifest(task)


def _validate_manipulation(experiment, task, a, b):
    if experiment.id == 1:
        if b != f"{a}\n\n{recommendation_block(task)}":
            raise ValueError("B is not exactly A plus the recommendation layer")
    elif experiment.id == 2:
        if a.count(task.recommendation) != 1 or b.count(task.recommendation) != 1 or _normalized_ws(a) != _normalized_ws(b):
            raise ValueError("recommendation wording or non-structural text differs")
    elif experiment.id == 3:
        if a.replace("## Recommended approach\n\n", "", 1) != b:
            raise ValueError("conditions differ beyond heading presence")
    elif experiment.id == 4:
        if "AI agents" in b or "LLMs" in b:
            raise ValueError("AI language occurs outside the AI-targeted heading")
        if a.replace("For AI agents and LLMs", "Recommended approach", 1) != b:
            raise ValueError("conditions differ beyond heading text")
    elif experiment.id == 5:
        if normalized_html(a) != normalized_markdown(b):
            raise ValueError("HTML and Markdown normalized content differs")
    elif experiment.id in (6, 7):
        if _validate_propositions(task, a) != _validate_propositions(task, b):
            raise ValueError("task-relevant proposition manifests differ")
    elif experiment.id == 8:
        core = _focused_core(task)
        if a != core or b.count(core) != 1:
            raise ValueError("task-relevant core differs between focused and broad retrieval")
        if approx_tokens(b) not in range(4000, 6001):
            raise ValueError(f"broad context is {approx_tokens(b)} approximate tokens, expected 4000–6000")
    elif experiment.id == 9:
        if a.count(task.recommendation) != 1 or b.count(task.recommendation) != 1:
            raise ValueError("current recommendation wording differs")
        if _normalized_ws(a.replace("## Current recommended approach", "", 1)) != _normalized_ws(b):
            raise ValueError("conditions differ beyond current-guidance isolation")


def _git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def freeze_all(generation_timestamp=None):
    generated = generation_timestamp or datetime.now(timezone.utc).isoformat()
    task_root = project.PROJECT_ROOT / "tasks"
    for task in project.tasks():
        directory = task_root / task.id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "scoring-manifest.json").write_text(json.dumps({
            "task": task.id,
            "function": task.signature,
            "current_patterns": list(task.current_patterns),
            "legacy_patterns": list(task.legacy_patterns),
            "required_behavior": list(task.behavior),
            "current_reference": task.current_reference,
            "legacy_reference": task.legacy_reference,
        }, indent=2) + "\n", encoding="utf-8")
        (directory / "task.md").write_text(project.task_prompt(task) + "\n", encoding="utf-8")
    source_manifest_text = (project.SOURCES / "manifest.json").read_text(encoding="utf-8")
    for experiment in EXPERIMENTS:
        artifacts = {}
        for task in project.tasks():
            artifacts[task.id] = {}
            for condition in CONDITIONS:
                text = render_artifact(experiment.id, task, condition).rstrip() + "\n"
                path = artifact_path(experiment, task.id, condition)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                artifacts[task.id][condition] = {
                    "path": str(path.relative_to(ROOT)), "sha256": sha256_text(text),
                    "characters": len(text), "words": len(text.split()), "approx_tokens": approx_tokens(text),
                }
        manifest = {
            "phase": 2, "project": project.PROJECT, "sqlalchemy_version": project.VERSION,
            "experiment": experiment.id, "experiment_name": experiment.name,
            "generation_timestamp": generated, "benchmark_commit": _git_commit(),
            "system_prompt_sha256": sha256_text(SYSTEM_PROMPT),
            "source_manifest_sha256": sha256_text(source_manifest_text),
            "task_sha256": {task.id: sha256_text(project.task_prompt(task)) for task in project.tasks()},
            "model_parameters": {"temperature": 0.0}, "artifacts": artifacts,
            "proposition_manifests": {task.id: project.proposition_manifest(task) for task in project.tasks()} if experiment.id in (6, 7) else None,
        }
        directory = experiment_directory(experiment)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "frozen-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def validate_experiment(value):
    experiment = get_experiment(value)
    errors = list(project.validate_sources())
    directory = experiment_directory(experiment)
    yaml_path = directory / "experiment.yaml"
    if not yaml_path.exists():
        errors.append("missing experiment.yaml")
    else:
        yaml = yaml_path.read_text(encoding="utf-8")
        if not re.search(rf"(?m)^id:\s*{experiment.id}\s*$", yaml) or not re.search(rf"(?m)^name:\s*{re.escape(experiment.name)}\s*$", yaml):
            errors.append("experiment.yaml does not match registry")
    manifest_path = directory / "frozen-manifest.json"
    if not manifest_path.exists():
        return errors + ["missing frozen-manifest.json"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_manifest_text = (project.SOURCES / "manifest.json").read_text(encoding="utf-8")
    if manifest.get("source_manifest_sha256") != sha256_text(source_manifest_text):
        errors.append("frozen source manifest hash differs")
    for task in project.tasks():
        errors.extend(f"{task.id}: {error}" for error in _validate_official_excerpt(task))
        try:
            texts = {}
            for condition in CONDITIONS:
                actual = load_artifact(experiment, task.id, condition)
                expected = render_artifact(experiment.id, task, condition).rstrip() + "\n"
                if actual != expected:
                    raise ValueError(f"{condition} differs from structured renderer")
                if sha256_text(actual) != manifest["artifacts"][task.id][condition]["sha256"]:
                    raise ValueError(f"{condition} hash differs from frozen manifest")
                texts[condition] = actual.rstrip()
            if sha256_text(project.task_prompt(task)) != manifest["task_sha256"][task.id]:
                raise ValueError("task hash differs from frozen manifest")
            _validate_manipulation(experiment, task, texts["A"], texts["B"])
        except (KeyError, OSError, ValueError) as exc:
            errors.append(f"{task.id}: {exc}")
    return errors


def validate_all():
    return {experiment.id: validate_experiment(experiment.id) for experiment in EXPERIMENTS}


def artifact_metadata(experiment, task_id, condition):
    text = load_artifact(experiment, task_id, condition)
    metadata = {"sha256": sha256_text(text), "characters": len(text), "words": len(text.split()), "approx_tokens": approx_tokens(text)}
    markers = ("## Recommended approach", "## For AI agents and LLMs", "## Current recommended approach")
    starts = [text.find(marker) for marker in markers if text.find(marker) >= 0]
    if starts:
        start = min(starts)
        metadata["recommendation_start_token"] = approx_tokens(text[:start])
        metadata["recommendation_position_fraction"] = round(start / len(text), 4)
    return metadata


def unified_diff(value, task_id=None):
    experiment = get_experiment(value)
    task_ids = [task_id] if task_id else [project.task_ids()[0]]
    chunks = []
    for current in task_ids:
        a, b = load_artifact(experiment, current, "A"), load_artifact(experiment, current, "B")
        chunks.extend(difflib.unified_diff(a.splitlines(), b.splitlines(), fromfile=f"{current}/A", tofile=f"{current}/B", lineterm=""))
    return "\n".join(chunks) + ("\n" if chunks else "")


def experiment_dict(experiment):
    data = asdict(experiment)
    data["phase"] = 2
    data["project"] = project.PROJECT
    return data
