import json
import os
import platform
import random
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .artifacts import artifact_metadata
from .evaluator import score
from .openrouter import complete, response_text
from .prompts import SYSTEM_PROMPT, documentation, sha256_text, task, user_prompt
from .worlds import CONDITIONS, all_worlds


def usage(response, key, fallback=0):
    return response.get("usage", {}).get(key, fallback)


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run(models, world_ids, conditions, repetitions, output, seed=None, resume=False):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is required for run")
    worlds = {world["id"]: world for world in all_worlds()}
    jobs = [(model, world_id, condition, trial) for model in models for world_id in world_ids for trial in range(1, repetitions + 1) for condition in conditions]
    random.Random(seed).shuffle(jobs)
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if resume and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                completed.add((row["model"], row["world"], row["condition"], row["trial"]))
        jobs = [job for job in jobs if job not in completed]
    commit = git_commit()
    with path.open("a" if resume else "w", encoding="utf-8") as sink:
        for model, world_id, condition, trial in jobs:
            user = user_prompt(world_id, condition)
            started = time.perf_counter()
            response = complete(model, SYSTEM_PROMPT, user, key)
            raw = response_text(response)
            result = score(worlds[world_id], raw)
            metadata = artifact_metadata(world_id, condition)
            input_tokens = usage(response, "prompt_tokens") or max(1, len(user) // 4)
            output_tokens = usage(response, "completion_tokens") or max(1, len(raw) // 4)
            row = {"run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(), "model": model, "world": world_id, "condition": condition, "trial": trial,
                   "artifact_sha256": metadata["sha256"], "artifact_metadata": metadata, "task_sha256": sha256_text(task(world_id)), "system_sha256": sha256_text(SYSTEM_PROMPT),
                   "prompt_tokens": input_tokens, "completion_tokens": output_tokens, "latency_ms": response.get("_latency_ms", round((time.perf_counter() - started) * 1000, 2)),
                   "cost_usd": response.get("usage", {}).get("cost", response.get("cost")), "raw_response": response, "raw_output": raw,
                   **result.as_dict(), "python_version": platform.python_version(), "benchmark_version": __version__, "git_commit": commit, "provider_metadata": response.get("provider"), "response_model": response.get("model"), "sampling": {"temperature": 0.0}}
            sink.write(json.dumps(row, ensure_ascii=False) + "\n"); sink.flush()
    return path
