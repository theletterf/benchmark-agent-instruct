from __future__ import annotations

import json, os, random, time, uuid
from datetime import datetime, timezone
from pathlib import Path

from . import CONDITIONS, PHASE, PROJECT, SYSTEM_PROMPT
from .project import RESULTS, TASK, artifact_path
from .scoring import score_response
from ..chain import safe_model_name
from ..env import load_dotenv
from ..openrouter import complete, response_text

def build():
    from .project import artifact
    for condition in CONDITIONS:
        path = artifact_path(condition); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(artifact(condition), encoding="utf-8")

def run(model, runs=3, output=None, seed=None, temperature=0.0, completion_fn=None):
    completion_fn = completion_fn or complete
    load_dotenv(); key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not key: raise RuntimeError("OPENROUTER_API_KEY is required")
    path = Path(output) if output else RESULTS / f"{safe_model_name(model)}-with-no-section-runs-{runs}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(condition, trial) for condition in CONDITIONS for trial in range(1, runs + 1)]
    random.Random(seed).shuffle(jobs)
    with path.open("w", encoding="utf-8") as out:
        for condition, trial in jobs:
            doc = artifact_path(condition).read_text()
            prompt = f"<DOCUMENTATION>\n{doc}</DOCUMENTATION>\n\n<TASK>\n{TASK}\n</TASK>"
            start = time.perf_counter(); response = completion_fn(model, SYSTEM_PROMPT, prompt, key, temperature=temperature)
            raw = response_text(response); usage = response.get("usage", {}); evaluation = score_response(raw)
            row = {"run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(), "phase": PHASE, "project": PROJECT, "model": model, "condition": condition, "trial": trial, "raw_output": raw, "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"), "cost_usd": usage.get("cost", response.get("cost")), "latency_ms": response.get("_latency_ms", round((time.perf_counter()-start)*1000,2)), **evaluation.as_dict()}
            out.write(json.dumps(row) + "\n"); out.flush()
    return path

def read(path): return [json.loads(line) for line in Path(path).read_text().splitlines() if line]
