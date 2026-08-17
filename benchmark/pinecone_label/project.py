from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..worlds import ROOT

ROOT_DIR = ROOT / "phase-4-pinecone-label"
SOURCES = ROOT_DIR / "sources"
ARTIFACTS = ROOT_DIR / "artifacts"
RESULTS = ROOT_DIR / "results"

TASK = """Write a Python function `bootstrap_and_search(pc)` that creates a `quickstart` integrated-embedding index if it is absent, loads two text records into namespace `docs`, and searches that namespace for the text `refund policy`. Return only the function. Do not configure credentials."""

BODY = """Use the current integrated-embedding quickstart pattern below. The index embeds the `content` field with `llama-text-embed-v2`; records use `_id` and `content`; search accepts text input and reranks results.

```python
if not pc.has_index("quickstart"):
    pc.create_index_for_model(
        name="quickstart", cloud="aws", region="us-east-1",
        embed={"model": "llama-text-embed-v2", "field_map": {"text": "content"}},
    )

index = pc.Index("quickstart")
index.upsert_records(
    namespace="docs",
    records=[{"_id": "rec1", "content": "Refund requests must be submitted within 30 days."}],
)
results = index.search(
    namespace="docs",
    query={"top_k": 5, "inputs": {"text": "refund policy"}},
    rerank={"model": "bge-reranker-v2-m3", "top_n": 3, "rank_fields": ["content"]},
)
```

The source quickstart explicitly distinguishes this pattern from dimension-based `create_index`, `upsert()`, and `query()` with `vector=`."""

DECISIONS = (
    ("index-creation", "create_index_for_model", "create_index("),
    ("record-ingestion", "upsert_records", "upsert("),
    ("text-search", "search(", "query("),
    ("text-inputs", "inputs", "vector"),
)


def manifest():
    return json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))


def source_path():
    return SOURCES / manifest()["sources"][0]["snapshot"]


def artifact(condition: str):
    heading = {"N": "", "G": "## Recommended quickstart\n\n", "AI": "## For AI agents and LLMs\n\n"}[condition]
    return f"# Pinecone quickstart\n\n{heading}{BODY}\n"


def artifact_path(condition: str):
    return ARTIFACTS / {"N": "no-section.md", "G": "recommended.md", "AI": "for-ai-agents.md"}[condition]


def validate():
    errors = []
    source = source_path()
    if not source.is_file():
        return ["missing frozen Pinecone quickstart"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest()["sources"][0]["sha256"]:
        errors.append("Pinecone source hash mismatch")
    n, g, ai = artifact_path("N"), artifact_path("G"), artifact_path("AI")
    if not n.is_file() or not g.is_file() or not ai.is_file():
        errors.append("missing label-study artifacts")
        return errors
    n_text, g_text, ai_text = n.read_text(), g.read_text(), ai.read_text()
    frozen = json.loads((ROOT_DIR / "manifests" / "frozen-artifacts.json").read_text(encoding="utf-8"))
    if hashlib.sha256(n_text.encode()).hexdigest() != frozen["no_section_sha256"]:
        errors.append("no-section artifact hash mismatch")
    if hashlib.sha256(g_text.encode()).hexdigest() != frozen["recommended_sha256"]:
        errors.append("recommended artifact hash mismatch")
    if hashlib.sha256(ai_text.encode()).hexdigest() != frozen["for_ai_agents_sha256"]:
        errors.append("AI-targeted artifact hash mismatch")
    if n_text.replace("\n\n", "\n\n## Recommended quickstart\n\n", 1) != g_text:
        errors.append("no-section and generic conditions differ beyond heading presence")
    if g_text.replace("## Recommended quickstart", "## For AI agents and LLMs", 1) != ai_text:
        errors.append("conditions differ beyond heading text")
    source_text = source.read_text()
    for token in ("create_index_for_model", "upsert_records", "search() with inputs", "query() with vector"):
        if token not in source_text:
            errors.append(f"frozen source does not support: {token}")
    return errors
