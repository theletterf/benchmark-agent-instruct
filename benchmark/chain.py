from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .experiments import CONDITIONS, approx_tokens, get_experiment, list_experiments, load_artifact, validate_experiment
from .prompts import SYSTEM_PROMPT, task
from .runner import run_experiment
from .worlds import world_ids


@dataclass
class ChainItem:
    experiment: int
    name: str
    calls: int
    approximate_input_tokens: int
    approximate_cost_usd: float | None = None


def selected_experiments(start=1, end=9):
    if not (1 <= start <= end <= 9):
        raise ValueError("chain range must satisfy 1 <= --from <= --to <= 9")
    return [experiment for experiment in list_experiments() if start <= experiment.id <= end]


def inspect_chain(model, runs=3, start=1, end=9):
    items = []
    for experiment in selected_experiments(start, end):
        token_total = 0
        for world_id in world_ids():
            for condition in CONDITIONS:
                prompt_chars = len(SYSTEM_PROMPT) + len(task(experiment, world_id)) + len(load_artifact(experiment, world_id, condition)) + 64
                token_total += approx_tokens("x" * prompt_chars) * runs
        items.append(ChainItem(experiment.id, experiment.name, len(world_ids()) * len(CONDITIONS) * runs, token_total))
    return items


def format_chain_inspection(model, runs=3, start=1, end=9):
    items = inspect_chain(model, runs, start, end)
    lines = [f"Model: {model}", f"Runs/world/condition: {runs}", "", "| Exp | Name | Calls | Approx. input tokens | Approx. cost |", "|---:|---|---:|---:|---:|"]
    for item in items:
        cost = "unavailable (offline)" if item.approximate_cost_usd is None else f"${item.approximate_cost_usd:.4f}"
        lines.append(f"| {item.experiment} | {item.name} | {item.calls} | {item.approximate_input_tokens:,} | {cost} |")
    lines.extend(["", f"Total calls: {sum(item.calls for item in items)}", f"Approximate input tokens: {sum(item.approximate_input_tokens for item in items):,}", "Approximate cost: unavailable without a current offline price entry."])
    return "\n".join(lines)


def safe_model_name(model):
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", model).strip("-")


def run_chain(model, runs=3, start=1, end=9, results_dir=Path("results/chain"), seed=None, allow_invalid=False):
    outputs = []
    base = Path(results_dir) / safe_model_name(model)
    for experiment in selected_experiments(start, end):
        errors = validate_experiment(experiment.id)
        if errors and not allow_invalid:
            raise RuntimeError(f"Experiment {experiment.id} failed validation:\n" + "\n".join(errors))
        output = base / f"{experiment.id:02d}-{experiment.name}-runs-{runs}.jsonl"
        run_experiment(experiment.id, model, world_ids(), runs, output, seed=seed, resume=True)
        outputs.append(output)
    return outputs
