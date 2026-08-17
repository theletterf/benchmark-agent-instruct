from __future__ import annotations

from dataclasses import dataclass

from .artifacts import CONDITIONS, EXPERIMENTS, approx_tokens, load_artifact, validate_experiment
from .projects import sqlalchemy as project
from .runner import REAL_SYSTEM_PROMPT, assess_headroom, experiment_output_path, find_calibration, read_jsonl, run_experiment


@dataclass
class ChainItem:
    experiment: int
    name: str
    calls: int
    approximate_input_tokens: int


def inspect_chain(model, runs=3):
    items = []
    for experiment in EXPERIMENTS:
        tokens = 0
        for task in project.tasks():
            for condition in CONDITIONS:
                chars = len(REAL_SYSTEM_PROMPT) + len(load_artifact(experiment, task.id, condition)) + len(project.task_prompt(task)) + 64
                tokens += approx_tokens("x" * chars) * runs
        items.append(ChainItem(experiment.id, experiment.name, len(project.tasks()) * 2 * runs, tokens))
    return items


def format_inspection(model, runs=3):
    items = inspect_chain(model, runs)
    calibration = find_calibration(model)
    lines = [f"Phase: 2 (real documentation)", f"Project: {project.PROJECT} {project.VERSION}", f"Model: {model}", f"Runs/task/condition: {runs}", "",
             "| Exp | Name | Tasks | Calls | Approx. input tokens |", "|---:|---|---:|---:|---:|"]
    for item in items:
        lines.append(f"| {item.experiment} | {item.name} | {len(project.tasks())} | {item.calls} | {item.approximate_input_tokens:,} |")
    lines.extend(["", f"Main-chain calls: {sum(item.calls for item in items)}", "Prior calibration calls at default: 10", f"Full Phase 2 progression: {sum(item.calls for item in items)+10}", f"Approximate main-chain input tokens: {sum(item.approximate_input_tokens for item in items):,}", "Estimated cost: unavailable without a current offline model price entry."])
    if calibration:
        assessment = assess_headroom(read_jsonl(calibration))
        lines.append(f"Calibration: {calibration} ({'insufficient headroom; main chain must stop' if assessment['insufficient_headroom'] else 'headroom available'})")
    else:
        lines.append("Calibration: not found; it must be run before any main experiment.")
    return "\n".join(lines)


def require_headroom(model):
    calibration = find_calibration(model)
    if not calibration:
        raise RuntimeError("prior calibration is required before Phase 2 experiments")
    assessment = assess_headroom(read_jsonl(calibration))
    if assessment["insufficient_headroom"]:
        raise RuntimeError("SQLAlchemy does not provide sufficient prior conflict for this model to cleanly test the real-document replication")
    return calibration, assessment


def run_chain(model, runs=3, seed=None, temperature=0.0):
    require_headroom(model)
    outputs = []
    for experiment in EXPERIMENTS:
        errors = validate_experiment(experiment.id)
        if errors:
            raise RuntimeError(f"Experiment {experiment.id} validation failed:\n" + "\n".join(errors))
        output = experiment_output_path(experiment, model, runs)
        outputs.append(run_experiment(experiment.id, model, project.task_ids(), runs, output, seed=seed, resume=True, temperature=temperature))
    return outputs
