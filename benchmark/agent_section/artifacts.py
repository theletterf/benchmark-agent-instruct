"""Build and validate realistic Phase 3 documentation bundles."""
from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import difflib
import json
import re
from pathlib import Path

from .project import (
    ARTIFACT_ROOT, MANIFEST_ROOT, artifact_path, diff_path, estimate_tokens,
    load_task, proposition_manifest, sha256_text, source_path, sources, tasks,
    validate_source_hashes,
)

BLOCK_START = "<!-- phase-3-for-agents:start -->"
BLOCK_END = "<!-- phase-3-for-agents:end -->"


class _MarkdownRenderer(HTMLParser):
    """Small deterministic HTML-to-readable-Markdown renderer for frozen docs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.in_pre = False
        self.in_code = False
        self.in_link = False
        self.link_href = ""
        self.link_text: list[str] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.table_rows: list[list[str]] = []
        self.in_table = False

    def _append(self, value: str) -> None:
        if self.cell is not None:
            self.cell.append(value)
        elif self.in_link:
            self.link_text.append(value)
        else:
            self.parts.append(value)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4"}:
            self._append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "p":
            self._append("\n\n")
        elif tag == "br":
            self._append("\n")
        elif tag == "li":
            self._append("\n- ")
        elif tag == "pre":
            self.in_pre = True
            self._append("\n\n```text\n")
        elif tag == "code" and not self.in_pre:
            self.in_code = True
            self._append("`")
        elif tag == "strong":
            self._append("**")
        elif tag == "em":
            self._append("*")
        elif tag == "a":
            self.in_link = True
            self.link_href = values.get("href", "")
            self.link_text = []
        elif tag == "table":
            self.in_table = True
            self.table_rows = []
            self._append("\n\n")
        elif tag == "tr" and self.in_table:
            self.row = []
        elif tag in {"th", "td"} and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_pre = False
            self._append("\n```\n")
        elif tag == "code" and not self.in_pre:
            self._append("`")
            self.in_code = False
        elif tag == "strong":
            self._append("**")
        elif tag == "em":
            self._append("*")
        elif tag == "a":
            text = "".join(self.link_text).strip()
            # Preserve the official prose but omit noisy navigation/self links.
            if text:
                self.parts.append(text)
            self.in_link = False
            self.link_href = ""
            self.link_text = []
        elif tag in {"th", "td"} and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table_rows.append(self.row)
            self.row = None
        elif tag == "table" and self.in_table:
            if self.table_rows:
                width = max(len(row) for row in self.table_rows)
                rows = [row + [""] * (width - len(row)) for row in self.table_rows]
                self.parts.append("| " + " | ".join(rows[0]) + " |\n")
                self.parts.append("| " + " | ".join(["---"] * width) + " |\n")
                for row in rows[1:]:
                    self.parts.append("| " + " | ".join(row) + " |\n")
            self.in_table = False
            self.table_rows = []
            self._append("\n")

    def handle_data(self, data):
        if self.in_pre:
            self._append(data)
        else:
            self._append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        result = "".join(self.parts)
        result = re.sub(r"[ \t]+\n", "\n", result)
        result = re.sub(r"\n{3,}", "\n\n", result)
        result = re.sub(r" +", " ", result)
        result = result.replace(" ` ", " `").replace(" `", " `")
        return unescape(result).strip()


def _heading_start(html: str, level: int, section: str) -> re.Match[str]:
    pattern = rf"<h{level}\b[^>]*\bid=(?:\"{re.escape(section)}\"|'{re.escape(section)}'|{re.escape(section)})(?:\s|>)"
    match = re.search(pattern, html, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"section anchor not found: {section}")
    return match


def extract_section(source_id: str, section: str) -> str:
    html = source_path(source_id).read_text(encoding="utf-8")
    if section == "__intro__":
        # Frozen project pages place the article body between the h1 and first h2.
        start = re.search(r"<h1\b", html, flags=re.IGNORECASE)
        if not start:
            raise ValueError(f"article heading not found in {source_id}")
        end = re.search(r"<h2\b", html[start.start():], flags=re.IGNORECASE)
        if not end:
            raise ValueError(f"first h2 not found in {source_id}")
        fragment = html[start.start():start.start() + end.start()]
    else:
        start = _heading_start(html, 2, section)
        end = re.search(r"<h2\b", html[start.end():], flags=re.IGNORECASE)
        stop = start.end() + end.start() if end else len(html)
        fragment = html[start.start():stop]
    parser = _MarkdownRenderer()
    parser.feed(fragment)
    rendered = parser.text()
    if not rendered:
        raise ValueError(f"empty extracted section: {source_id}#{section}")
    return rendered


def normal_artifact(task_id: str) -> str:
    task = load_task(task_id)
    source_records = sources()
    used = []
    sections = []
    for bundle in task.source_sections:
        record = source_records[bundle["source_id"]]
        used.append(record)
        for section in bundle["sections"]:
            rendered = extract_section(bundle["source_id"], section)
            sections.append(
                f"<!-- source: {bundle['source_id']}#{section} -->\n{rendered}"
            )
    header = [
        f"# Documentation bundle — {task.title}",
        "",
        "Frozen authoritative OpenTelemetry documentation. Source sections are preserved in source order.",
        "",
        "Sources:",
    ]
    seen = set()
    for record in used:
        if record["id"] in seen:
            continue
        seen.add(record["id"])
        header.append(
            f"- {record['title']} — {record['url']} "
            f"({record['document_version']}, retrieved {record['retrieval_date']})"
        )
    return "\n".join(header) + "\n\n---\n\n" + "\n\n---\n\n".join(sections) + "\n"


def treatment_artifact(task_id: str, normal: str | None = None) -> str:
    task = load_task(task_id)
    normal = normal if normal is not None else normal_artifact(task_id)
    marker = "\n---\n\n"
    head, body = normal.split(marker, 1)
    block = f"{BLOCK_START}\n## For agents\n\n{task.agent_section}\n{BLOCK_END}"
    return head + "\n\n" + block + marker + body


def remove_agent_block(treatment: str) -> str:
    pattern = r"\n\n" + re.escape(BLOCK_START) + r"\n## For agents\n\n.*?\n" + re.escape(BLOCK_END)
    cleaned, count = re.subn(pattern, "", treatment, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("treatment must contain exactly one complete For agents block")
    return cleaned


def build_artifacts() -> None:
    for directory in ("normal", "for-agents", "diffs"):
        (ARTIFACT_ROOT / directory).mkdir(parents=True, exist_ok=True)
    for task in tasks():
        normal = normal_artifact(task.id)
        treatment = treatment_artifact(task.id, normal)
        artifact_path(task.id, "A").write_text(normal, encoding="utf-8")
        artifact_path(task.id, "B").write_text(treatment, encoding="utf-8")
        diff = "".join(difflib.unified_diff(
            normal.splitlines(keepends=True), treatment.splitlines(keepends=True),
            fromfile=f"normal/{task.id}.md", tofile=f"for-agents/{task.id}.md",
        ))
        diff_path(task.id).write_text(diff, encoding="utf-8")


def token_metrics(task_id: str) -> dict[str, int | float]:
    normal = artifact_path(task_id, "A").read_text(encoding="utf-8")
    total = artifact_path(task_id, "B").read_text(encoding="utf-8")
    section = "## For agents\n\n" + load_task(task_id).agent_section + "\n"
    normal_tokens = estimate_tokens(normal)
    section_tokens = estimate_tokens(section)
    total_tokens = estimate_tokens(total)
    return {
        "normal_documentation_tokens": normal_tokens,
        "agent_section_tokens": section_tokens,
        "treatment_tokens": total_tokens,
        "percentage_context_increase": round((total_tokens - normal_tokens) / normal_tokens * 100, 2),
    }


def _normalized(value: str) -> str:
    value = re.sub(r"[`*#|“”\"']", " ", value)
    value = re.sub(r"\s+([.,;:])", r"\1", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def validate_propositions(task_id: str) -> list[str]:
    errors: list[str] = []
    normal = artifact_path(task_id, "A").read_text(encoding="utf-8")
    manifest = proposition_manifest(task_id)
    if manifest.get("task") != task_id:
        errors.append(f"{task_id}: proposition manifest task mismatch")
    stated = " ".join(item["proposition"].strip() for item in manifest.get("agent_instructions", []))
    if _normalized(stated) != _normalized(load_task(task_id).agent_section):
        errors.append(f"{task_id}: proposition text does not reconstruct the frozen agent section")
    for index, item in enumerate(manifest.get("agent_instructions", []), 1):
        if not item.get("supported_by"):
            errors.append(f"{task_id}: proposition {index} has no source support")
        for support in item.get("supported_by", []):
            marker = f"<!-- source: {support['source']}#{support['section']} -->"
            if marker not in normal:
                errors.append(f"{task_id}: proposition {index} references absent {marker}")
                continue
            section_text = normal.split(marker, 1)[1].split("<!-- source:", 1)[0]
            if _normalized(support["quote"]) not in _normalized(section_text):
                errors.append(f"{task_id}: proposition {index} support quote not found in Condition A")
    return errors


def validate_all() -> list[str]:
    errors = validate_source_hashes()
    for task in tasks():
        normal_path = artifact_path(task.id, "A")
        treatment_path = artifact_path(task.id, "B")
        if not normal_path.is_file() or not treatment_path.is_file():
            errors.append(f"{task.id}: missing generated A/B artifact")
            continue
        normal = normal_path.read_text(encoding="utf-8")
        treatment = treatment_path.read_text(encoding="utf-8")
        try:
            stripped = remove_agent_block(treatment)
        except ValueError as exc:
            errors.append(f"{task.id}: {exc}")
        else:
            if stripped.encode("utf-8") != normal.encode("utf-8"):
                errors.append(f"{task.id}: documentation outside agent block is not byte-identical")
        expected_normal = normal_artifact(task.id)
        if expected_normal != normal:
            errors.append(f"{task.id}: normal artifact drifted from frozen source/task definition")
        if treatment_artifact(task.id, normal) != treatment:
            errors.append(f"{task.id}: treatment artifact drifted from normal + frozen block")
        word_count = len(load_task(task.id).agent_section.split())
        if not 75 <= word_count <= 200:
            errors.append(f"{task.id}: For agents block has {word_count} words (expected 75–200)")
        try:
            errors.extend(validate_propositions(task.id))
        except FileNotFoundError:
            errors.append(f"{task.id}: missing proposition manifest")
    frozen_path = MANIFEST_ROOT / "frozen-artifacts.json"
    if not frozen_path.is_file():
        errors.append("missing frozen artifact manifest")
    else:
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        records = {item["task"]: item for item in frozen.get("tasks", [])}
        for task in tasks():
            record = records.get(task.id)
            if not record:
                errors.append(f"{task.id}: absent from frozen artifact manifest")
                continue
            normal = artifact_path(task.id, "A").read_text(encoding="utf-8")
            treatment = artifact_path(task.id, "B").read_text(encoding="utf-8")
            expected = {
                "task_sha256": sha256_text(task.prompt),
                "normal_sha256": sha256_text(normal),
                "for_agents_sha256": sha256_text(treatment),
                "shared_documentation_sha256": sha256_text(remove_agent_block(treatment)),
                "agent_section_sha256": sha256_text(task.agent_section),
            }
            for name, value in expected.items():
                if record.get(name) != value:
                    errors.append(f"{task.id}: frozen manifest mismatch for {name}")
    return errors


def write_frozen_manifest() -> Path:
    payload = {"project": "opentelemetry", "tasks": []}
    for task in tasks():
        normal = artifact_path(task.id, "A").read_text(encoding="utf-8")
        treatment = artifact_path(task.id, "B").read_text(encoding="utf-8")
        payload["tasks"].append({
            "task": task.id,
            "task_sha256": sha256_text(task.prompt),
            "normal_sha256": sha256_text(normal),
            "for_agents_sha256": sha256_text(treatment),
            "shared_documentation_sha256": sha256_text(remove_agent_block(treatment)),
            "agent_section_sha256": sha256_text(task.agent_section),
            "diff_sha256": sha256_text(diff_path(task.id).read_text(encoding="utf-8")),
            "tokens": token_metrics(task.id),
        })
    path = MANIFEST_ROOT / "frozen-artifacts.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
