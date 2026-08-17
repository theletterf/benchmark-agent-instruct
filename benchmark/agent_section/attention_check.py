"""Separate non-production attention-check follow-up for Phase 3."""
from __future__ import annotations

import difflib
import json
import os
import platform
import random
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .artifacts import BLOCK_END
from . import PHASE, PROJECT, SYSTEM_PROMPT
from .project import PHASE_ROOT, artifact_path, estimate_tokens, sha256_text, tasks
from .runner import read_jsonl, user_prompt
from .scoring import parse_json_response, score_response
from .. import __version__
from ..chain import safe_model_name
from ..env import load_dotenv
from ..experiments import git_commit
from ..openrouter import complete, response_text

ROOT = PHASE_ROOT / "follow-ups" / "attention-check"
MANIFEST = ROOT / "manifests.json"
START = "<!-- phase-3-attention-check:start -->"
END = "<!-- phase-3-attention-check:end -->"


def manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def artifact_path_h(task_id):
    return ROOT / "artifacts" / f"{task_id}.md"


def attention_artifact(task_id):
    base = artifact_path(task_id, "B").read_text(encoding="utf-8")
    instruction = manifest()["counterfactuals"][task_id]["instruction"]
    block = f"{START}\n\n### Benchmark attention check — non-production\n\n{instruction}\n\n{END}\n"
    if base.count(BLOCK_END) != 1:
        raise ValueError(f"{task_id}: expected one For agents block")
    return base.replace(BLOCK_END + "\n", block + BLOCK_END + "\n", 1)


def build():
    (ROOT / "artifacts").mkdir(parents=True, exist_ok=True)
    (ROOT / "diffs").mkdir(parents=True, exist_ok=True)
    for task in tasks():
        base = artifact_path(task.id, "B").read_text(encoding="utf-8")
        output = attention_artifact(task.id)
        artifact_path_h(task.id).write_text(output, encoding="utf-8")
        diff = "".join(difflib.unified_diff(base.splitlines(keepends=True), output.splitlines(keepends=True), fromfile=f"for-agents/{task.id}.md", tofile=f"attention-check/{task.id}.md"))
        (ROOT / "diffs" / f"{task.id}.diff").write_text(diff, encoding="utf-8")


def strip_attention_check(text):
    pattern = re.escape(START) + r"\n\n### Benchmark attention check — non-production\n\n.*?\n\n" + re.escape(END) + r"\n"
    output, count = re.subn(pattern, "", text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("expected exactly one marked attention-check block")
    return output


def validate():
    errors = []
    if manifest().get("not_a_documentation_intervention") is not True:
        errors.append("attention check must be explicitly non-production")
    for task in tasks():
        path = artifact_path_h(task.id)
        if not path.is_file():
            errors.append(f"missing attention artifact: {task.id}")
            continue
        base = artifact_path(task.id, "B").read_text(encoding="utf-8")
        try:
            stripped = strip_attention_check(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{task.id}: {exc}")
        else:
            if stripped.encode() != base.encode():
                errors.append(f"{task.id}: H differs from B outside attention-check block")
    return errors


def _at_path(payload, path):
    for key in path:
        if not isinstance(payload, dict):
            return None
        payload = payload.get(key)
    return payload


def attention_score(task_id, response):
    payload = parse_json_response(response)
    checks = manifest()["counterfactuals"][task_id]["decisions"]
    followed = 0
    for check in checks:
        value = _at_path(payload, check["path"])
        if "key" in check:
            value = value.get(check["key"]) if isinstance(value, dict) else None
        if str(value).strip().casefold() == str(check["value"]).strip().casefold():
            followed += 1
    return {"attention_check_decisions": len(checks), "attention_check_followed": followed, "attention_check_rate": followed / len(checks) if checks else 0.0}


def attention_plan(smoke=False, runs=3, seed=None):
    selected = tasks()[:2] if smoke else tasks()
    repetitions = 1 if smoke else runs
    jobs = [(task, condition, trial) for task in selected for condition in ("B", "H") for trial in range(1, repetitions + 1)]
    random.Random(seed).shuffle(jobs)
    return jobs


def default_output(model, smoke, runs):
    suffix = "smoke" if smoke else f"runs-{runs}"
    return ROOT / "results" / f"{safe_model_name(model)}-{suffix}.jsonl"


def run_attention_check(model, runs=3, smoke=False, output=None, seed=None, temperature=0.0, completion_fn=None):
    if runs < 1:
        raise ValueError("runs must be at least 1")
    completion_fn = completion_fn or complete
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if completion_fn is complete and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required in the shell environment or project .env")
    path = output or default_output(model, smoke, runs)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for task, condition, trial in attention_plan(smoke, runs, seed):
            documentation = artifact_path(task.id, "B").read_text(encoding="utf-8") if condition == "B" else artifact_path_h(task.id).read_text(encoding="utf-8")
            prompt = user_prompt(documentation, task.prompt)
            started = time.perf_counter()
            response = completion_fn(model, SYSTEM_PROMPT, prompt, api_key, temperature=temperature)
            raw = response_text(response)
            evaluation = score_response(task.id, raw)
            usage = response.get("usage", {})
            row = {
                "run_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(),
                "phase": PHASE, "project": PROJECT, "experiment": "attention-check", "model": model,
                "task": task.id, "trial": trial, "condition": condition,
                "condition_label": "existing For agents" if condition == "B" else "For agents + non-production counterfactual",
                "system_sha256": sha256_text(SYSTEM_PROMPT), "task_sha256": sha256_text(task.prompt),
                "documentation_sha256": sha256_text(documentation),
                "prompt_tokens": usage.get("prompt_tokens") or estimate_tokens(prompt),
                "completion_tokens": usage.get("completion_tokens") or estimate_tokens(raw),
                "latency_ms": response.get("_latency_ms", round((time.perf_counter() - started) * 1000, 2)),
                "cost_usd": usage.get("cost", response.get("cost")), "raw_output": raw, "raw_response": response,
                **evaluation.as_dict(), **attention_score(task.id, raw),
                "benchmark_version": __version__, "benchmark_commit": git_commit(), "python_version": platform.python_version(),
            }
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
    return path


def write_attention_report(jsonl_path, output=None):
    rows = read_jsonl(jsonl_path)
    groups = {condition: [row for row in rows if row["condition"] == condition] for condition in ("B", "H")}
    lines = ["# Phase 3 follow-up — attention check", "", "This is an instruction-conflict diagnostic, not a documentation-quality result.", "", "| Condition | Responses | Current/correct decisions | Counterfactual followed |", "| --- | ---: | ---: | ---: |"]
    for condition, values in groups.items():
        total = sum(row["total_decisions"] for row in values)
        current = sum(row["current_correct_decisions"] for row in values)
        attention_total = sum(row["attention_check_decisions"] for row in values)
        attention = sum(row["attention_check_followed"] for row in values)
        lines.append(f"| {condition} | {len(values)} | {current / total:.1%} | {attention / attention_total:.1%} |" if total and attention_total else f"| {condition} | {len(values)} | n/a | n/a |")
    lines += ["", "H asks for deliberately counterfactual output. A high H counterfactual-followed rate means the marked block was acted on in this conflict setting; it does not demonstrate that agent-oriented documentation is beneficial or trustworthy.", ""]
    target = output or Path(jsonl_path).with_suffix(".md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    return target
