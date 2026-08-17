from __future__ import annotations

import json
import os
import platform
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import PHASE
from .artifacts import CONDITIONS, artifact_metadata, get_experiment, load_artifact, sha256_text, validate_experiment
from .fixture import evaluate_output
from .projects import sqlalchemy as project
from .. import __version__
from ..chain import safe_model_name
from ..env import load_dotenv
from ..experiments import git_commit
from ..openrouter import complete, response_text

REAL_SYSTEM_PROMPT = "Return only the requested Python implementation. When documentation is supplied, treat it as authoritative."


def result_root():
    return Path("results") / "phase-2" / project.PROJECT


def calibration_output_path(model, runs=2):
    return result_root() / "calibration" / f"{safe_model_name(model)}-runs-{runs}.jsonl"


def experiment_output_path(experiment, model, runs):
    return result_root() / safe_model_name(model) / f"{experiment.id:02d}-{experiment.name}-runs-{runs}.jsonl"


def experimental_user_prompt(experiment, task, condition):
    documentation = load_artifact(experiment, task.id, condition)
    return f"<DOCUMENTATION>\n{documentation}</DOCUMENTATION>\n\n<TASK>\n{project.task_prompt(task)}\n</TASK>"


def calibration_user_prompt(task):
    return project.task_prompt(task)


def _usage(response, key, fallback=0):
    return response.get("usage", {}).get(key, fallback)


def _invoke(completion_fn, model, user, api_key, temperature):
    started = time.perf_counter()
    response = completion_fn(model, REAL_SYSTEM_PROMPT, user, api_key, temperature=temperature)
    raw = response_text(response)
    return response, raw, response.get("_latency_ms", round((time.perf_counter() - started) * 1000, 2))


def _common_row(model, task, trial, response, raw, evaluation, user, latency, temperature):
    return {
        "run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": PHASE, "project": project.PROJECT, "model": model, "task": task.id,
        "trial": trial, "sqlalchemy_version": project.VERSION,
        "task_sha256": sha256_text(project.task_prompt(task)),
        "system_sha256": sha256_text(REAL_SYSTEM_PROMPT),
        "prompt_tokens": _usage(response, "prompt_tokens") or max(1, len(user) // 4),
        "completion_tokens": _usage(response, "completion_tokens") or max(1, len(raw) // 4),
        "latency_ms": latency, "cost_usd": response.get("usage", {}).get("cost", response.get("cost")),
        "raw_output": raw, "raw_response": response, **evaluation.as_dict(),
        "sampling": {"requested_temperature": temperature, "temperature_sent": response.get("_temperature_sent", temperature)},
        "model_parameters": {"temperature": temperature}, "response_model": response.get("model"),
        "provider_metadata": response.get("provider"), "benchmark_version": __version__,
        "benchmark_commit": git_commit(), "python_version": platform.python_version(),
    }


def run_calibration(model, repetitions=2, output=None, seed=None, temperature=0.0, completion_fn=None):
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or project .env")
    path = Path(output) if output else calibration_output_path(model, repetitions)
    path.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(task, trial) for task in project.tasks() for trial in range(1, repetitions + 1)]
    random.Random(seed).shuffle(jobs)
    with path.open("w", encoding="utf-8") as sink:
        for task, trial in jobs:
            user = calibration_user_prompt(task)
            response, raw, latency = _invoke(completion_fn, model, user, api_key, temperature)
            evaluation = evaluate_output(task, raw)
            row = _common_row(model, task, trial, response, raw, evaluation, user, latency, temperature)
            row.update({"calibration": True, "experiment": None, "experiment_name": "prior-calibration", "condition": "no-documentation", "condition_code": None, "documentation_sha256": None})
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")
            sink.flush()
    return path


def _completed(path, experiment, model):
    complete_jobs = set()
    if not path.exists():
        return complete_jobs
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid resume JSON at {path}:{number}") from exc
        if row.get("phase") != 2 or row.get("experiment") != experiment.id or row.get("model") != model:
            raise RuntimeError("resume file contains another phase, experiment, or model")
        condition = row["condition_code"]
        metadata = artifact_metadata(experiment, row["task"], condition)
        if row.get("documentation_sha256") != metadata["sha256"]:
            raise RuntimeError(f"frozen documentation changed for {row['task']} {condition}")
        complete_jobs.add((row["task"], condition, int(row["trial"])))
    return complete_jobs


def run_experiment(experiment_value, model, task_ids, repetitions=3, output=None, seed=None, resume=False, temperature=0.0, completion_fn=None):
    experiment = get_experiment(experiment_value)
    errors = validate_experiment(experiment.id)
    if errors:
        raise RuntimeError("Phase 2 experiment validation failed:\n" + "\n".join(errors))
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or project .env")
    path = Path(output) if output else experiment_output_path(experiment, model, repetitions)
    path.parent.mkdir(parents=True, exist_ok=True)
    done = _completed(path, experiment, model) if resume else set()
    tasks = {task.id: task for task in project.tasks()}
    jobs = [(task_id, condition, trial) for task_id in task_ids for condition in CONDITIONS for trial in range(1, repetitions + 1) if (task_id, condition, trial) not in done]
    random.Random(seed).shuffle(jobs)
    with path.open("a" if resume else "w", encoding="utf-8") as sink:
        for task_id, condition, trial in jobs:
            task = tasks[task_id]
            user = experimental_user_prompt(experiment, task, condition)
            response, raw, latency = _invoke(completion_fn, model, user, api_key, temperature)
            evaluation = evaluate_output(task, raw)
            metadata = artifact_metadata(experiment, task_id, condition)
            row = _common_row(model, task, trial, response, raw, evaluation, user, latency, temperature)
            row.update({
                "calibration": False, "experiment": experiment.id, "experiment_name": experiment.name,
                "condition": experiment.condition_label(condition), "condition_code": condition,
                "documentation_sha256": metadata["sha256"], "documentation_metadata": metadata,
            })
            sink.write(json.dumps(row, ensure_ascii=False) + "\n")
            sink.flush()
    return path


def read_jsonl(path):
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{number}") from exc
    return rows


def assess_headroom(rows, threshold=0.8):
    results = []
    for task in project.tasks():
        subset = [row for row in rows if row.get("task") == task.id]
        current = sum(row.get("api_classification") == "current" for row in subset)
        legacy = sum(row.get("api_classification") == "legacy" for row in subset)
        mixed = sum(row.get("api_classification") == "mixed" for row in subset)
        rate = current / len(subset) if subset else 0.0
        results.append({"task": task.id, "n": len(subset), "current": current, "legacy": legacy, "mixed": mixed, "current_rate": rate, "weak_headroom": bool(subset) and rate >= threshold})
    return {"tasks": results, "insufficient_headroom": bool(results) and all(item["weak_headroom"] for item in results)}


def find_calibration(model):
    directory = result_root() / "calibration"
    candidates = sorted(directory.glob(f"{safe_model_name(model)}-runs-*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None
