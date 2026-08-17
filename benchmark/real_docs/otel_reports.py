from __future__ import annotations

import csv
import json
from pathlib import Path

from .otel_runner import assess_headroom, find_calibration, read_jsonl, task_summary
from .projects import opentelemetry as project


def write_candidate_report(output=None):
    path = Path(output or project.PROJECT_ROOT / "candidates" / "candidate-report.md")
    lines = ["# OpenTelemetry candidate prior conflicts", "", "Frozen official sources, not model recall, define all historical/current mappings.", "", "| Candidate | Historical form | Current form | Source |", "|---|---|---|---|"]
    for item in project.candidates():
        lines.append(f"| {item['id']} | `{item['historical']}` | `{item['current']}` | {item['source']} |")
    lines += ["", "## Proposed calibration tasks", ""]
    for task in project.tasks():
        lines.append(f"- `{task.id}` — {task.title}: {len(task.decisions)} independently scored decisions.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_calibration_report(rows, jsonl):
    path = Path(jsonl)
    stage = rows[0]["calibration_stage"] if rows else "unknown"
    summaries = [task_summary(rows, task.id) for task in project.tasks()]
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    lines = [f"# OpenTelemetry {stage} calibration", "", f"Model: {rows[0]['model'] if rows else 'unknown'}", "", "Decision-level currentness is primary; fully-current responses are reported separately.", "", "| Task | Responses | Current decisions | Fully current | Mixed responses |", "|---|---:|---:|---:|---:|"]
    for item in summaries:
        lines.append(f"| {item['task']} | {item['responses']} | {item['current_decisions']}/{item['decisions']} ({item['current_decision_rate']:.1%}) | {item['fully_current_responses']}/{item['responses']} ({item['fully_current_rate']:.1%}) | {item['mixed_responses']} |")
    lines += ["", "This diagnostic is not Experiment 0."]
    md_path = path.with_suffix(".md")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path


def write_headroom_report(model, output=None):
    prior_path, docs_path = find_calibration(model, "prior"), find_calibration(model, "docs")
    if not prior_path or not docs_path:
        missing = ", ".join(stage for stage, path in (("prior", prior_path), ("docs", docs_path)) if not path)
        raise RuntimeError(f"missing required OpenTelemetry calibration stage(s): {missing}")
    assessment = assess_headroom(read_jsonl(prior_path), read_jsonl(docs_path))
    path = Path(output or (Path("results") / "phase-2" / project.PROJECT / "headroom" / f"{model.replace('/', '-')}.md"))
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# OpenTelemetry headroom assessment", "", f"Model: {model}", "", "| Candidate task | No docs | Official docs | Remaining headroom | Status |", "|---|---:|---:|---:|---|"]
    for item in assessment["tasks"]:
        lines.append(f"| {item['task']} | {item['prior']['current_decision_rate']:.1%} | {item['docs']['current_decision_rate']:.1%} | {item['remaining_headroom']:.1%} | {item['status']} |")
    lines += ["", f"Overall no-doc current-decision rate: {assessment['prior_current_decision_rate']:.1%}.", f"Overall official-doc current-decision rate: {assessment['docs_current_decision_rate']:.1%}.", f"Overall suitability: {'GOOD — freeze eligible tasks before generating experiments' if assessment['suitable'] else 'INSUFFICIENT — do not generate the structural battery'}."]
    if assessment["reason"]:
        lines += ["", assessment["reason"]]
    lines += ["", "Eligible task IDs: " + (", ".join(assessment["eligible_tasks"]) or "none")]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, assessment
