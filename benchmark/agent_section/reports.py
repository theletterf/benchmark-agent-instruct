"""Descriptive Phase 3 reports; phases are never statistically pooled."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .artifacts import token_metrics
from .project import decisions, tasks
from .runner import read_jsonl


def _aggregate(rows: list[dict]) -> dict:
    decision_rows = [decision for row in rows for decision in row.get("decisions", [])]
    total = len(decision_rows)
    current = sum(item["classification"] == "current" for item in decision_rows)
    historical = sum(item["classification"] == "historical" for item in decision_rows)
    invalid = sum(item["classification"] == "invalid" for item in decision_rows)
    mixed_decisions = sum(item["classification"] == "mixed" for item in decision_rows)
    responses = len(rows)
    fully = sum(bool(row.get("fully_correct")) for row in rows)
    mixed = sum(bool(row.get("mixed_current_historical")) for row in rows)
    return {
        "responses": responses, "decisions": total, "current": current,
        "historical": historical, "invalid": invalid, "mixed_decisions": mixed_decisions,
        "current_rate": current / total if total else 0.0,
        "historical_rate": historical / total if total else 0.0,
        "invalid_rate": invalid / total if total else 0.0,
        "fully_rate": fully / responses if responses else 0.0,
        "mixed_rate": mixed / responses if responses else 0.0,
    }


def _table(groups: dict[str, list[dict]], first_column: str) -> list[str]:
    lines = [
        f"| {first_column} | Responses | Decisions | Current/correct | Fully correct | Mixed | Historical | Invalid |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, rows in groups.items():
        value = _aggregate(rows)
        lines.append(
            f"| {name} | {value['responses']} | {value['decisions']} | {value['current_rate']:.1%} | "
            f"{value['fully_rate']:.1%} | {value['mixed_rate']:.1%} | {value['historical_rate']:.1%} | {value['invalid_rate']:.1%} |"
        )
    return lines


def render_report(rows: list[dict], source: str = "results") -> str:
    by_condition = {condition: [row for row in rows if row.get("condition") == condition] for condition in ("A", "B")}
    by_task = defaultdict(list)
    by_model = defaultdict(list)
    for row in rows:
        by_task[row["task"]].append(row)
        by_model[row["model"]].append(row)
    condition_stats = {key: _aggregate(value) for key, value in by_condition.items()}
    difference = (condition_stats["B"]["current_rate"] - condition_stats["A"]["current_rate"]) * 100
    overhead = [token_metrics(task.id) for task in tasks()]
    normal_tokens = sum(item["normal_documentation_tokens"] for item in overhead)
    section_tokens = sum(item["agent_section_tokens"] for item in overhead)
    treatment_tokens = sum(item["treatment_tokens"] for item in overhead)
    efficiency = difference / (section_tokens / len(overhead) / 100) if section_tokens else 0.0
    ceiling = bool(by_condition["A"]) and condition_stats["A"]["current_rate"] >= .95
    if not rows:
        interpretation = "No result rows were supplied; this is a report structure check only."
    elif difference > 1:
        interpretation = "Adding the complete dedicated agent-oriented summary improved behavior. This does not identify which mechanism caused the improvement."
    elif difference < -1:
        interpretation = "The added section may have harmed behavior or introduced conflicting emphasis. Inspect decision-level errors before drawing conclusions."
    else:
        interpretation = "No meaningful benefit was detected under these tasks and models."
    lines = [
        "# Phase 3 — For agents intervention", "", "## Question", "",
        "Does adding a dedicated `For agents` section to otherwise unchanged documentation improve agent behavior?", "",
        "## Corpus", "",
        "Frozen authoritative OpenTelemetry documentation and migration guidance. The five control artifacts use coherent page sections rather than answer-only excerpts.", "",
        "## Tasks", "",
    ]
    for task in tasks():
        lines.append(f"- **{task.title}** — {len(decisions(task.id))} independently scored decisions")
    lines += [
        "", "## Intervention", "", "Condition A: normal documentation", "", "Condition B: the same documentation plus one concise `For agents` synthesis", "",
        "## Validation", "", "A/B artifacts are accepted only when removing the marked agent block from B reproduces A byte-for-byte and every proposition has support in A.", "",
        "## Results", "",
    ]
    lines += _table({"A — Normal docs": by_condition["A"], "B — + For agents": by_condition["B"]}, "Condition")
    lines += ["", "## By task", ""] + _table(dict(sorted(by_task.items())), "Task")
    lines += ["", "## By model", ""] + _table(dict(sorted(by_model.items())), "Model")
    lines += [
        "", "## Effect", "", f"Decision-level difference: **{difference:+.1f} percentage points** (B − A).", "",
        "## Token overhead", "", f"Normal docs, total across five artifacts: {normal_tokens} estimated tokens.",
        f"Agent sections, total: {section_tokens} estimated tokens.", f"Treatment artifacts, total: {treatment_tokens} estimated tokens.",
        f"Descriptive efficiency: {efficiency:+.2f} percentage points per 100 additional estimated input tokens (using mean section cost).", "",
        "| Task | Normal docs | Agent section | Treatment | Context increase |", "| --- | ---: | ---: | ---: | ---: |",
    ]
    for task, metric in zip(tasks(), overhead):
        lines.append(f"| {task.id} | {metric['normal_documentation_tokens']} | {metric['agent_section_tokens']} | {metric['treatment_tokens']} | {metric['percentage_context_increase']:.2f}% |")
    lines += [
        "", "## Interpretation", "", interpretation, "",
        "The intervention bundles repetition, synthesis, explicit recommendation, isolation, and audience targeting. This phase does not decompose them.", "",
        "## Ceiling diagnostics", "", "**CONTROL CEILING**" if ceiling else "The aggregate control was below the 95% decision-level ceiling threshold.", "",
        "If controls saturate, first assess whether the complete bundle resembles documentation a real agent would receive; do not weaken correct documentation merely to create headroom.", "",
        "## Comparison with earlier phases", "",
        "- Phase 1 — fables: explicit recommendation strongly changed behavior, then ceiling.",
        "- Phase 2 — SQLAlchemy/OpenTelemetry: ordinary focused documentation often corrected behavior to ceiling.",
        "- Phase 3 — realistic normal docs vs the same docs plus `For agents`: tests whether the practical intervention adds value.", "",
        "The phases are not statistically pooled.", "", "## Caveats", "",
        "- Token counts are stable four-UTF-8-bytes-per-token estimates; provider-reported counts are retained in result rows.",
        "- Five tasks and three repetitions are a quick intervention test, not a broad population estimate.",
        "- A detected effect would justify, but does not itself answer, later mechanism experiments.",
        f"- Input results: `{source}`.", "",
    ]
    return "\n".join(lines)


def write_report(jsonl: Path, output: Path | None = None) -> Path:
    rows = read_jsonl(jsonl)
    target = Path(output) if output else Path(jsonl).with_suffix(".md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_report(rows, str(jsonl)), encoding="utf-8")
    return target
