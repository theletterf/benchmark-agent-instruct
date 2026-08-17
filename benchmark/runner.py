from __future__ import annotations

import json
import os
import platform
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .env import load_dotenv
from .evaluator import score
from .experiments import CONDITIONS, artifact_metadata, get_experiment, git_commit
from .openrouter import complete, response_text
from .prompts import SYSTEM_PROMPT, sha256_text, task, user_prompt
from .worlds import WORLD_VERSION, load_world


def _usage(response, key, fallback=0):
    return response.get("usage", {}).get(key, fallback)


def _completed_jobs(path, experiment, model):
    completed = set()
    if not path.exists():
        return completed
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"cannot resume: invalid JSON on {path}:{line_number}") from exc
        if row.get("experiment") != experiment.id or row.get("model") != model:
            raise RuntimeError(f"cannot resume: {path} contains another experiment or model")
        metadata = artifact_metadata(experiment, row["world"], row["condition"])
        if row.get("artifact_sha256") != metadata["sha256"]:
            raise RuntimeError(f"cannot resume: frozen artifact changed for {row['world']} {row['condition']}")
        completed.add((row["world"], row["condition"], int(row["trial"])))
    return completed


def run_experiment(
    experiment_value,
    model,
    world_ids,
    repetitions,
    output,
    seed=None,
    resume=False,
    temperature=0.0,
    completion_fn=None,
):
    experiment = get_experiment(experiment_value)
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or a project .env file")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = _completed_jobs(path, experiment, model) if resume else set()
    jobs = [
        (world_id, condition, trial)
        for world_id in world_ids
        for trial in range(1, repetitions + 1)
        for condition in CONDITIONS
        if (world_id, condition, trial) not in completed
    ]
    random.Random(seed).shuffle(jobs)
    commit = git_commit()
    mode = "a" if resume else "w"
    with path.open(mode, encoding="utf-8") as sink:
        for world_id, condition, trial in jobs:
            world = load_world(world_id)
            user = user_prompt(experiment, world_id, condition)
            started = time.perf_counter()
            response = completion_fn(model, SYSTEM_PROMPT, user, api_key, temperature=temperature)
            raw = response_text(response)
            result = score(world, raw)
            metadata = artifact_metadata(experiment, world_id, condition)
            input_tokens = _usage(response, "prompt_tokens") or max(1, len(user) // 4)
            output_tokens = _usage(response, "completion_tokens") or max(1, len(raw) // 4)
            row = {
                "run_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "experiment": experiment.id,
                "experiment_name": experiment.name,
                "model": model,
                "world": world_id,
                "world_version": WORLD_VERSION,
                "condition": condition,
                "condition_name": experiment.condition_label(condition),
                "trial": trial,
                "artifact_sha256": metadata["sha256"],
                "artifact_metadata": metadata,
                "system_sha256": sha256_text(SYSTEM_PROMPT),
                "task_sha256": sha256_text(task(experiment, world_id)),
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "latency_ms": response.get("_latency_ms", round((time.perf_counter() - started) * 1000, 2)),
                "cost_usd": response.get("usage", {}).get("cost", response.get("cost")),
                "raw_output": raw,
                "raw_response": response,
                **result.as_dict(),
                "sampling": {
                    "requested_temperature": temperature,
                    "temperature_sent": response.get("_temperature_sent", temperature),
                },
                "model_parameters": {"temperature": temperature},
                "provider_metadata": response.get("provider"),
                "response_model": response.get("model"),
                "benchmark_commit": commit,
                "benchmark_version": __version__,
                "python_version": platform.python_version(),
            }
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")
            sink.flush()
    return path


def run_calibration(model, repetitions, output, seed=None, completion_fn=None):
    """Run Experiment 1's neutral artifact only, recording diagnostic calibration rows."""
    experiment = get_experiment(1)
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or a project .env file")
    jobs = [(world_id, trial) for world_id in ["bellwater", "lantern", "messenger", "orchard", "well"] for trial in range(1, repetitions + 1)]
    random.Random(seed).shuffle(jobs)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as sink:
        for world_id, trial in jobs:
            world = load_world(world_id)
            user = user_prompt(experiment, world_id, "A")
            response = completion_fn(model, SYSTEM_PROMPT, user, api_key, temperature=0.0)
            raw = response_text(response)
            metadata = artifact_metadata(experiment, world_id, "A")
            row = {
                "run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
                "experiment": "calibration", "experiment_name": "neutral-calibration", "model": model,
                "world": world_id, "world_version": WORLD_VERSION, "condition": "neutral", "trial": trial,
                "artifact_sha256": metadata["sha256"], "artifact_metadata": metadata,
                "system_sha256": sha256_text(SYSTEM_PROMPT), "task_sha256": sha256_text(task(experiment, world_id)),
                "prompt_tokens": _usage(response, "prompt_tokens") or max(1, len(user) // 4),
                "completion_tokens": _usage(response, "completion_tokens") or max(1, len(raw) // 4),
                "latency_ms": response.get("_latency_ms"), "cost_usd": response.get("usage", {}).get("cost", response.get("cost")),
                "raw_output": raw, "raw_response": response, **score(world, raw).as_dict(),
                "sampling": {"requested_temperature": 0.0, "temperature_sent": response.get("_temperature_sent", 0.0)},
            }
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")
            sink.flush()
    return path
