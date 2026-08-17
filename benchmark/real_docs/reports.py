from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .artifacts import EXPERIMENTS, artifact_metadata, get_experiment
from .projects import sqlalchemy as project
from .runner import assess_headroom, find_calibration, read_jsonl, result_root
from ..stats import fisher, wilson


def _pct(k, n):
    return round(100 * k / n, 2) if n else 0.0


def _group_summary(rows, model, task, condition):
    n = len(rows)
    classes = {name: sum(row.get("api_classification") == name for row in rows) for name in ("current", "legacy", "mixed", "unclassified")}
    current_ci = wilson(classes["current"], n)
    return {
        "model": model, "task": task, "condition": condition, "n": n,
        "current_count": classes["current"], "current_pct": _pct(classes["current"], n),
        "current_wilson_low": current_ci[0], "current_wilson_high": current_ci[1],
        "legacy_count": classes["legacy"], "legacy_pct": _pct(classes["legacy"], n),
        "mixed_count": classes["mixed"], "mixed_pct": _pct(classes["mixed"], n),
        "unclassified_count": classes["unclassified"], "unclassified_pct": _pct(classes["unclassified"], n),
        "syntax_success_count": sum(bool(row.get("syntax_success")) for row in rows),
        "runtime_success_count": sum(bool(row.get("runtime_success")) for row in rows),
        "functional_correct_count": sum(bool(row.get("functional_correct")) for row in rows),
        "mean_prompt_tokens": round(sum(row.get("prompt_tokens") or 0 for row in rows) / n, 2) if n else 0,
        "total_cost_usd": round(sum(row.get("cost_usd") or 0 for row in rows), 6),
    }


def summarize(rows):
    groups = defaultdict(list)
    aggregates = defaultdict(list)
    for row in rows:
        key = (row["model"], row["task"], row["condition_code"])
        groups[key].append(row)
        aggregates[(row["model"], "ALL", row["condition_code"])].append(row)
    return [_group_summary(group, *key) for key, group in sorted(aggregates.items())] + [_group_summary(group, *key) for key, group in sorted(groups.items())]


def _comparison(rows, model):
    a = [row for row in rows if row["model"] == model and row["condition_code"] == "A"]
    b = [row for row in rows if row["model"] == model and row["condition_code"] == "B"]
    ak = sum(row["api_classification"] == "current" for row in a)
    bk = sum(row["api_classification"] == "current" for row in b)
    ap, bp = _pct(ak, len(a)), _pct(bk, len(b))
    return {"a_n": len(a), "b_n": len(b), "a_current": ak, "b_current": bk, "a_pct": ap, "b_pct": bp,
            "difference_b_minus_a_pp": round(bp - ap, 2), "fisher_p": fisher(ak, len(a)-ak, bk, len(b)-bk) if a and b else None,
            "ceiling": ap == 100 and bp == 100, "high_ceiling_risk": ap >= 90 and bp >= 90}


def write_calibration_report(rows, jsonl):
    assessment = assess_headroom(rows)
    path = Path(jsonl)
    csv_path = path.with_suffix(".csv")
    fields = ["task", "n", "current", "legacy", "mixed", "current_rate", "weak_headroom"]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(assessment["tasks"])
    lines = ["# SQLAlchemy prior calibration", "", f"Model: {rows[0]['model'] if rows else 'unknown'}", "", "Task-only prompts; no documentation was supplied. This diagnostic is not Experiment 0.", "",
             "| Task | N | Current | Legacy | Mixed | Headroom warning |", "|---|---:|---:|---:|---:|---|"]
    for item in assessment["tasks"]:
        lines.append(f"| {item['task']} | {item['n']} | {item['current']} ({_pct(item['current'], item['n']):.1f}%) | {item['legacy']} | {item['mixed']} | {'weak (≥80% current)' if item['weak_headroom'] else 'available'} |")
    lines.extend(["", "## Headroom assessment", "", "SQLAlchemy does not provide sufficient prior conflict for this model to cleanly test the real-document replication." if assessment["insufficient_headroom"] else "At least one task retains behavioral headroom; the main Phase 2 chain may proceed without changing frozen prompts.", ""])
    md_path = path.with_suffix(".md")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def _phase1_analogue(experiment):
    return f"Phase 1 Experiment {experiment.id} manipulated {experiment.independent_variable} in a fictional world. Phase 2 preserves that independent variable while using frozen SQLAlchemy 2.x documentation and executable ORM tasks."


def _artifact_size_lines(experiment):
    if experiment.id not in (5, 6, 7, 8):
        return []
    lines = ["## Artifact token sizes", "", "Approximate artifact tokens use the same character-based estimator before provider execution.", "",
             "| Task | A tokens | B tokens | B vs A reduction | A recommendation position | B recommendation position |",
             "|---|---:|---:|---:|---:|---:|"]
    for task in project.tasks():
        a = artifact_metadata(experiment, task.id, "A"); b = artifact_metadata(experiment, task.id, "B")
        reduction = 100 * (a["approx_tokens"] - b["approx_tokens"]) / a["approx_tokens"]
        lines.append(f"| {task.id} | {a['approx_tokens']} | {b['approx_tokens']} | {reduction:.1f}% | {a.get('recommendation_position_fraction', 'n/a')} | {b.get('recommendation_position_fraction', 'n/a')} |")
    return lines + [""]


def write_experiment_report(rows, jsonl, experiment_value):
    if not rows:
        raise ValueError("cannot report empty results")
    experiment = get_experiment(experiment_value)
    if any(row.get("phase") != 2 or row.get("experiment") != experiment.id for row in rows):
        raise ValueError("results contain another phase or experiment")
    path = Path(jsonl)
    summaries = summarize(rows)
    fields = list(summaries[0])
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(summaries)
    model = rows[0]["model"]
    comparison = _comparison(rows, model)
    calibration_path = find_calibration(model)
    calibration = assess_headroom(read_jsonl(calibration_path)) if calibration_path else None
    aggregate = [row for row in summaries if row["task"] == "ALL"]
    lines = [f"# Experiment {experiment.id} — {experiment.title}", "", "## Research question", "", experiment.research_question, "",
             "## Phase 1 analogue", "", _phase1_analogue(experiment), "", "## Real-document manipulation", "", f"Condition A: {experiment.condition_a}. Condition B: {experiment.condition_b}. The independent variable is {experiment.independent_variable}.", "",
             "## Source material", "", f"SQLAlchemy {project.VERSION}; frozen official ORM SELECT, Session, migration, and Legacy Query documentation. Source URLs and SHA-256 hashes are recorded in the project source manifest.", "",
             "## Prior calibration", ""]
    if calibration:
        total_n = sum(item["n"] for item in calibration["tasks"]); total_current = sum(item["current"] for item in calibration["tasks"])
        lines.append(f"No-documentation current-pattern selection: {_pct(total_current, total_n):.1f}% ({total_current}/{total_n}).")
    else:
        lines.append("No matching calibration result was found; the main chain should not be interpreted as a prior-shift analysis.")
    lines.extend(["", "## Results", "", "| Condition | N | Current (Wilson 95%) | Legacy | Mixed | Unclassified |", "|---|---:|---:|---:|---:|---:|"])
    for row in aggregate:
        label = experiment.condition_label(row["condition"])
        lines.append(f"| {row['condition']} — {label} | {row['n']} | {row['current_count']} ({row['current_pct']:.1f}%) [{row['current_wilson_low']:.1f}, {row['current_wilson_high']:.1f}] | {row['legacy_count']} ({row['legacy_pct']:.1f}%) | {row['mixed_count']} | {row['unclassified_count']} |")
    lines.extend(["", f"Current-pattern difference (B − A): {comparison['difference_b_minus_a_pp']:+.2f} percentage points. Fisher's exact p = {comparison['fisher_p']}.", "",
                  "## By task", "", "| Task | Condition | N | Current | Legacy | Mixed | Functional |", "|---|---|---:|---:|---:|---:|---:|"])
    for row in summaries:
        if row["task"] == "ALL": continue
        lines.append(f"| {row['task']} | {row['condition']} | {row['n']} | {row['current_count']} ({row['current_pct']:.1f}%) | {row['legacy_count']} | {row['mixed_count']} | {row['functional_correct_count']} ({_pct(row['functional_correct_count'], row['n']):.1f}%) |")
    lines.extend([""] + _artifact_size_lines(experiment))
    lines.extend(["", "## Functional correctness", "", f"Syntax success: {sum(r['syntax_success'] for r in rows)}/{len(rows)}. Runtime success: {sum(r['runtime_success'] for r in rows)}/{len(rows)}. Functional correctness: {sum(r['functional_correct'] for r in rows)}/{len(rows)}.", "",
                  "## Current vs legacy selection", "", "API-family classification is AST-based and reported separately from executable correctness; working legacy answers remain legacy.", "",
                  "## Token usage", "", f"Provider-reported prompt tokens: {sum(r.get('prompt_tokens') or 0 for r in rows):,}. Completion tokens: {sum(r.get('completion_tokens') or 0 for r in rows):,}.", "",
                  "## Ceiling diagnostics", ""])
    if comparison["ceiling"]:
        lines.append("No detectable difference under a ceiling condition (100% vs 100%).")
    elif comparison["high_ceiling_risk"]:
        lines.append("Both conditions are at or above 90%; this comparison has high ceiling risk.")
    else:
        lines.append("The aggregate comparison is not at the predefined high-ceiling threshold.")
    lines.extend(["", "## Interpretation", "", "Interpret the direct contrast together with task-level variation and the prior calibration. Calibration is descriptive and is not a third randomized condition.", "", "## Caveats", "", "Five API decisions limit generalization. Temperature-zero repetitions may be correlated. Runtime success under pinned SQLite does not establish suitability for every database or application.", ""])
    md_path = path.with_suffix(".md")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def _collect_phase2(results):
    rows = []
    for path in Path(results).rglob("*.jsonl"):
        rows.extend(row for row in read_jsonl(path) if row.get("phase") == 2 and row.get("experiment") is not None)
    return rows


def write_phase2_summary(results=None, output=None):
    root = Path(results) if results else result_root()
    rows = _collect_phase2(root)
    models = sorted({row["model"] for row in rows})
    lines = ["# Phase 2 — Real documentation experiment chain", ""]
    for model in models:
        lines.extend([f"## Model: {model}", "", "| Exp | Question | A current | B current | Difference | Ceiling |", "|---:|---|---:|---:|---:|---|"])
        for experiment in EXPERIMENTS:
            subset = [row for row in rows if row["model"] == model and row["experiment"] == experiment.id]
            if not subset:
                lines.append(f"| {experiment.id} | {experiment.title} | — | — | — | not run |")
                continue
            comparison = _comparison(subset, model)
            ceiling = "100% ceiling" if comparison["ceiling"] else "high risk" if comparison["high_ceiling_risk"] else "no"
            lines.append(f"| {experiment.id} | {experiment.title} | {comparison['a_pct']:.1f}% | {comparison['b_pct']:.1f}% | {comparison['difference_b_minus_a_pp']:+.1f} pp | {ceiling} |")
        lines.append("")
    output_path = Path(output) if output else root / "phase-2-summary.md"
    output_path.parent.mkdir(parents=True, exist_ok=True); output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _collect_phase1(results):
    rows = []
    root = Path(results)
    for path in root.rglob("*.jsonl"):
        if "phase-2" in path.parts: continue
        rows.extend(row for row in read_jsonl(path) if row.get("phase") in (None, 1) and isinstance(row.get("experiment"), int))
    return rows


def write_cross_phase_report(phase1_results="results", phase2_results=None, output=None):
    p1 = _collect_phase1(phase1_results)
    p2 = _collect_phase2(phase2_results or result_root())
    models = sorted({row["model"] for row in p1} & {row["model"] for row in p2})
    lines = ["# Phase 1 vs Phase 2", "", "This is a descriptive comparison of matched independent variables, not a pooled statistical test.", ""]
    for model in models:
        lines.extend([f"## Model: {model}", "", "| Exp | Question | Phase 1 effect | Phase 2 effect |", "|---:|---|---:|---:|"])
        for experiment in EXPERIMENTS:
            one = [row for row in p1 if row["model"] == model and row["experiment"] == experiment.id]
            two = [row for row in p2 if row["model"] == model and row["experiment"] == experiment.id]
            if not one or not two:
                lines.append(f"| {experiment.id} | {experiment.title} | {'not run' if not one else 'available'} | {'not run' if not two else 'available'} |")
                continue
            a1=[r for r in one if r["condition"]=="A"]; b1=[r for r in one if r["condition"]=="B"]
            p1a=_pct(sum(r["preferred_path"] for r in a1),len(a1)); p1b=_pct(sum(r["preferred_path"] for r in b1),len(b1)); d1=p1b-p1a
            c2=_comparison(two,model)
            label1=(f"preserved ({d1:+.1f} pp)" if experiment.id in (6, 7) and d1 >= 0 else f"{d1:+.1f} pp") + (" / ceiling" if p1a>=90 and p1b>=90 else "")
            label2=(f"preserved ({c2['difference_b_minus_a_pp']:+.1f} pp)" if experiment.id in (6, 7) and c2['difference_b_minus_a_pp'] >= 0 else f"{c2['difference_b_minus_a_pp']:+.1f} pp") + (" / ceiling" if c2["high_ceiling_risk"] else "")
            lines.append(f"| {experiment.id} | {experiment.title} | {label1} | {label2} |")
        calibration_path=find_calibration(model)
        exp1=[r for r in p2 if r["model"]==model and r["experiment"]==1]
        if calibration_path and exp1:
            cal=read_jsonl(calibration_path); no_docs=_pct(sum(r["api_classification"]=="current" for r in cal),len(cal))
            comp=_comparison(exp1,model)
            lines.extend(["", "### Prior shift", "", f"No documentation: {no_docs:.1f}% current → official documentation: {comp['a_pct']:.1f}% → explicit recommendation: {comp['b_pct']:.1f}%.",
                          f"Documentation shift: {comp['a_pct']-no_docs:+.1f} pp. Experimental lift: {comp['difference_b_minus_a_pp']:+.1f} pp. Total correction: {comp['b_pct']-no_docs:+.1f} pp.", ""])
    output_path = Path(output) if output else result_root() / "phase-1-vs-phase-2.md"
    output_path.parent.mkdir(parents=True, exist_ok=True); output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
