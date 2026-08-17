"""Two-stage, decision-level OpenTelemetry candidate calibration."""
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
from .otel_scoring import score_response
from .projects import opentelemetry as project
from .. import __version__
from ..chain import safe_model_name
from ..env import load_dotenv
from ..experiments import git_commit
from ..openrouter import complete, response_text

OTEL_SYSTEM_PROMPT = "Answer the user's telemetry task directly. When documentation is supplied, use it as authoritative. Return only the requested compact mapping."


def result_root():
    return Path("results") / "phase-2" / project.PROJECT


def calibration_output_path(model, stage, runs):
    return result_root() / "calibration" / f"{safe_model_name(model)}-{stage}-runs-{runs}.jsonl"


def user_prompt(task, stage):
    if stage == "prior":
        return task.prompt
    if stage == "docs":
        return f"<DOCUMENTATION>\n{task.official_excerpt}\n</DOCUMENTATION>\n\n<TASK>\n{task.prompt}\n</TASK>"
    raise ValueError(f"unknown calibration stage: {stage}")


def _invoke(completion_fn, model, user, api_key, temperature):
    started = time.perf_counter()
    response = completion_fn(model, OTEL_SYSTEM_PROMPT, user, api_key, temperature=temperature)
    return response, response_text(response), response.get("_latency_ms", round((time.perf_counter() - started) * 1000, 2))


def run_calibration(model, stage, repetitions=3, output=None, seed=None, temperature=0.0, completion_fn=None):
    if stage not in {"prior", "docs"}:
        raise ValueError("stage must be 'prior' or 'docs'")
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or project .env")
    path = Path(output) if output else calibration_output_path(model, stage, repetitions)
    path.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(task, trial) for task in project.tasks() for trial in range(1, repetitions + 1)]
    random.Random(seed).shuffle(jobs)
    with path.open("w", encoding="utf-8") as stream:
        for task, trial in jobs:
            user = user_prompt(task, stage)
            response, raw, latency = _invoke(completion_fn, model, user, api_key, temperature)
            evaluation = score_response(task, raw)
            row = {
                "run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
                "phase": PHASE, "project": project.PROJECT, "model": model, "task": task.id,
                "trial": trial, "calibration": True, "calibration_stage": stage,
                "experiment": None, "experiment_name": f"opentelemetry-{stage}-calibration",
                "condition": "no-documentation" if stage == "prior" else "official-documentation",
                "condition_code": None, "task_sha256": __import__("hashlib").sha256(task.prompt.encode()).hexdigest(),
                "system_sha256": __import__("hashlib").sha256(OTEL_SYSTEM_PROMPT.encode()).hexdigest(),
                "documentation_sha256": None if stage == "prior" else __import__("hashlib").sha256(task.official_excerpt.encode()).hexdigest(),
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens") or max(1, len(user) // 4),
                "completion_tokens": response.get("usage", {}).get("completion_tokens") or max(1, len(raw) // 4),
                "latency_ms": latency, "cost_usd": response.get("usage", {}).get("cost", response.get("cost")),
                "raw_output": raw, "raw_response": response, **evaluation.as_dict(),
                "sampling": {"requested_temperature": temperature, "temperature_sent": response.get("_temperature_sent", temperature)},
                "model_parameters": {"temperature": temperature}, "response_model": response.get("model"),
                "provider_metadata": response.get("provider"), "benchmark_version": __version__,
                "benchmark_commit": git_commit(), "python_version": platform.python_version(),
                "scoring_revision": 3,
            }
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    return path


def rescore_calibration(path, output=None):
    """Create a revisioned calibration file without overwriting raw records."""
    source = Path(path)
    target = Path(output) if output else source.with_name(source.stem + "-rescored-r3.jsonl")
    tasks = {task.id: task for task in project.tasks()}
    rows = read_jsonl(source)
    with target.open("w", encoding="utf-8") as stream:
        for row in rows:
            evaluation = score_response(tasks[row["task"]], row["raw_output"])
            for key in ("decisions", "current_decisions", "historical_decisions", "mixed_response", "fully_current", "current_decision_rate"):
                row[key] = evaluation.as_dict()[key]
            row["scoring_revision"] = 3
            row["rescored_from"] = str(source)
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return target


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def find_calibration(model, stage):
    directory = result_root() / "calibration"
    candidates = sorted(directory.glob(f"{safe_model_name(model)}-{stage}-runs-*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def task_summary(rows, task_id):
    rows = [row for row in rows if row["task"] == task_id]
    decisions = [decision for row in rows for decision in row.get("decisions", [])]
    current = sum(decision["classification"] == "current" for decision in decisions)
    historical = sum(decision["classification"] == "historical" for decision in decisions)
    return {
        "task": task_id, "responses": len(rows), "decisions": len(decisions), "current_decisions": current,
        "historical_decisions": historical, "current_decision_rate": current / len(decisions) if decisions else 0.0,
        "fully_current_responses": sum(bool(row.get("fully_current")) for row in rows),
        "fully_current_rate": sum(bool(row.get("fully_current")) for row in rows) / len(rows) if rows else 0.0,
        "mixed_responses": sum(bool(row.get("mixed_response")) for row in rows),
    }


def assess_headroom(prior_rows, docs_rows):
    tasks = []
    for task in project.tasks():
        prior = task_summary(prior_rows, task.id)
        docs = task_summary(docs_rows, task.id)
        docs_rate = docs["current_decision_rate"]
        if docs_rate >= .95:
            status = "saturated"
        elif .20 <= prior["current_decision_rate"] <= .85:
            status = "eligible"
        elif prior["current_decision_rate"] < .20:
            status = "strong-historical-prior"
        else:
            status = "high-prior-ceiling-risk"
        tasks.append({"task": task.id, "prior": prior, "docs": docs, "remaining_headroom": 1 - docs_rate, "status": status})
    prior_decisions = sum(item["prior"]["decisions"] for item in tasks)
    docs_decisions = sum(item["docs"]["decisions"] for item in tasks)
    prior_current = sum(item["prior"]["current_decisions"] for item in tasks)
    docs_current = sum(item["docs"]["current_decisions"] for item in tasks)
    docs_rate = docs_current / docs_decisions if docs_decisions else 0.0
    eligible = [item["task"] for item in tasks if item["status"] in {"eligible", "strong-historical-prior"} and item["docs"]["current_decision_rate"] < .95]
    return {
        "tasks": tasks, "prior_current_decision_rate": prior_current / prior_decisions if prior_decisions else 0.0,
        "docs_current_decision_rate": docs_rate, "remaining_headroom": 1 - docs_rate,
        "eligible_tasks": eligible, "suitable": bool(eligible) and docs_rate < .95,
        "reason": "OpenTelemetry documentation corrected the historical prior almost completely, leaving insufficient headroom for the structural battery." if docs_rate >= .95 else None,
    }
