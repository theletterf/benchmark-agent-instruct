"""Two-condition Phase 3 OpenRouter runner."""
from __future__ import annotations

import json
import os
import platform
import random
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import CONDITIONS, PHASE, PROJECT, SYSTEM_PROMPT
from .project import RESULT_ROOT, artifact_path, estimate_tokens, sha256_text, tasks
from .scoring import score_response
from .. import __version__
from ..chain import safe_model_name
from ..env import load_dotenv
from ..experiments import git_commit
from ..openrouter import complete, response_text


def user_prompt(documentation: str, task_prompt: str) -> str:
    return f"<DOCUMENTATION>\n{documentation}\n</DOCUMENTATION>\n\n<TASK>\n{task_prompt}\n</TASK>"


def plan(smoke: bool = False, runs: int = 3, seed: int | None = None):
    selected = tasks()[:2] if smoke else tasks()
    repetitions = 1 if smoke else runs
    jobs = [
        (task, condition, trial)
        for task in selected
        for condition in CONDITIONS
        for trial in range(1, repetitions + 1)
    ]
    random.Random(seed).shuffle(jobs)
    return jobs


def default_output(model: str, smoke: bool, runs: int) -> Path:
    suffix = "smoke" if smoke else f"runs-{runs}"
    return RESULT_ROOT / f"{safe_model_name(model)}-{suffix}.jsonl"


def _invoke(completion_fn, model, user, api_key, temperature):
    started = time.perf_counter()
    response = completion_fn(model, SYSTEM_PROMPT, user, api_key, temperature=temperature)
    latency = response.get("_latency_ms", round((time.perf_counter() - started) * 1000, 2))
    return response, response_text(response), latency


def run_experiment(
    model: str, runs: int = 3, smoke: bool = False, output: Path | None = None,
    seed: int | None = None, temperature: float = 0.0,
    completion_fn: Callable | None = None,
) -> Path:
    if runs < 1:
        raise ValueError("runs must be at least 1")
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or project .env")
    path = Path(output) if output else default_output(model, smoke, runs)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for task, condition, trial in plan(smoke=smoke, runs=runs, seed=seed):
            documentation = artifact_path(task.id, condition).read_text(encoding="utf-8")
            prompt = user_prompt(documentation, task.prompt)
            response, raw, latency = _invoke(completion_fn, model, prompt, api_key, temperature)
            evaluation = score_response(task.id, raw)
            usage = response.get("usage", {})
            row = {
                "run_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "phase": PHASE, "project": PROJECT, "experiment": "agent-section",
                "model": model, "task": task.id, "trial": trial,
                "condition": condition,
                "condition_label": "normal documentation" if condition == "A" else "normal documentation + For agents",
                "system_prompt": SYSTEM_PROMPT,
                "system_sha256": sha256_text(SYSTEM_PROMPT),
                "task_sha256": sha256_text(task.prompt),
                "documentation_sha256": sha256_text(documentation),
                "prompt_tokens": usage.get("prompt_tokens") or estimate_tokens(prompt),
                "completion_tokens": usage.get("completion_tokens") or estimate_tokens(raw),
                "latency_ms": latency,
                "cost_usd": usage.get("cost", response.get("cost")),
                "raw_output": raw, "raw_response": response,
                **evaluation.as_dict(),
                "sampling": {"requested_temperature": temperature, "temperature_sent": response.get("_temperature_sent", temperature)},
                "response_model": response.get("model"), "provider_metadata": response.get("provider"),
                "benchmark_version": __version__, "benchmark_commit": git_commit(),
                "python_version": platform.python_version(), "scoring_revision": 1,
            }
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    return path


def serialize_result(path: Path, row: dict) -> None:
    """Small public seam used by tests and result repair tools."""
    Path(path).write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
