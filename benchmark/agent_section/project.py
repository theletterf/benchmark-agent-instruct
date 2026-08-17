"""Frozen Phase 3 corpus and task definitions."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ..worlds import ROOT

PHASE_ROOT = ROOT / "phase-3-agent-section"
SOURCE_ROOT = PHASE_ROOT / "sources"
TASK_ROOT = PHASE_ROOT / "tasks"
MANIFEST_ROOT = PHASE_ROOT / "manifests"
ARTIFACT_ROOT = PHASE_ROOT / "artifacts"
RESULT_ROOT = PHASE_ROOT / "results"
REPORT_ROOT = PHASE_ROOT / "reports"

TASK_ORDER = (
    "http-client-telemetry",
    "http-server-telemetry",
    "http-client-duration",
    "database-client-telemetry",
    "java-agent-configuration",
)


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    prompt: str
    source_sections: tuple[dict[str, Any], ...]
    agent_section: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def source_manifest() -> dict[str, Any]:
    return _load_json(SOURCE_ROOT / "manifest.json")


def sources() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in source_manifest()["sources"]}


def source_path(source_id: str) -> Path:
    record = sources()[source_id]
    return SOURCE_ROOT / record["snapshot"]


def load_task(task_id: str) -> Task:
    payload = _load_json(TASK_ROOT / f"{task_id}.json")
    return Task(
        id=payload["id"], title=payload["title"], prompt=payload["prompt"],
        source_sections=tuple(payload["source_sections"]),
        agent_section=payload["agent_section"],
    )


def tasks() -> tuple[Task, ...]:
    return tuple(load_task(task_id) for task_id in TASK_ORDER)


def decision_manifest(task_id: str) -> dict[str, Any]:
    return _load_json(MANIFEST_ROOT / "decisions" / f"{task_id}.json")


def decisions(task_id: str) -> tuple[dict[str, Any], ...]:
    return tuple(decision_manifest(task_id)["decisions"])


def proposition_manifest(task_id: str) -> dict[str, Any]:
    return _load_json(MANIFEST_ROOT / "propositions" / f"{task_id}.json")


def artifact_path(task_id: str, condition: str) -> Path:
    directory = "normal" if condition == "A" else "for-agents"
    return ARTIFACT_ROOT / directory / f"{task_id}.md"


def diff_path(task_id: str) -> Path:
    return ARTIFACT_ROOT / "diffs" / f"{task_id}.diff"


def estimate_tokens(text: str) -> int:
    """Stable, dependency-free input-token estimate (four UTF-8 bytes/token)."""
    return max(1, math.ceil(len(text.encode("utf-8")) / 4))


def validate_source_hashes() -> list[str]:
    errors: list[str] = []
    for item in source_manifest()["sources"]:
        path = SOURCE_ROOT / item["snapshot"]
        if not path.is_file():
            errors.append(f"missing frozen source: {path}")
            continue
        actual = sha256_bytes(path.read_bytes())
        if actual != item["sha256"]:
            errors.append(f"source hash mismatch for {item['id']}: {actual}")
    return errors
