from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from .experiments import artifact_metadata, get_experiment, list_experiments
from .stats import fisher, wilson
from .worlds import world_ids

METRICS = ("world_correct", "preferred_path", "alternative_path", "mixed_path", "invalid_answer", "sequence_correct")


def read_jsonl(path):
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{number}") from exc
    return rows


def _pct(k, n):
    return round(100 * k / n, 2) if n else 0.0


def _mean(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float)) and not isinstance(row.get(key), bool)]
    return round(sum(values) / len(values), 3) if values else None


def _summary(group, model, world, condition):
    n = len(group)
    result = {"model": model, "world": world, "condition": condition, "n": n}
    for metric in METRICS:
        count = sum(bool(row.get(metric)) for row in group)
        result[f"{metric}_count"] = count
        result[f"{metric}_pct"] = _pct(count, n)
        if metric == "preferred_path":
            low, high = wilson(count, n)
            result["preferred_wilson_low"] = low
            result["preferred_wilson_high"] = high
    result.update({
        "mean_prompt_tokens": _mean(group, "prompt_tokens"),
        "mean_completion_tokens": _mean(group, "completion_tokens"),
        "mean_latency_ms": _mean(group, "latency_ms"),
        "total_cost_usd": round(sum(row.get("cost_usd") or 0 for row in group), 6),
    })
    return result


def summarize(rows, include_aggregate=True):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["model"], row["world"], row["condition"])].append(row)
    summaries = [_summary(group, *key) for key, group in sorted(groups.items())]
    if include_aggregate:
        aggregates = defaultdict(list)
        for row in rows:
            aggregates[(row["model"], "ALL", row["condition"])].append(row)
        summaries = [_summary(group, *key) for key, group in sorted(aggregates.items())] + summaries
    return summaries


def _comparison(rows, model):
    a = [row for row in rows if row["model"] == model and row["condition"] == "A"]
    b = [row for row in rows if row["model"] == model and row["condition"] == "B"]
    ak = sum(bool(row["preferred_path"]) for row in a)
    bk = sum(bool(row["preferred_path"]) for row in b)
    return {
        "a_n": len(a), "b_n": len(b), "a_preferred": ak, "b_preferred": bk,
        "difference_b_minus_a_pp": round(_pct(bk, len(b)) - _pct(ak, len(a)), 2),
        "fisher_p": fisher(ak, len(a) - ak, bk, len(b) - bk) if a and b else None,
    }


def _format_count(row, metric):
    return f"{row[f'{metric}_count']} ({row[f'{metric}_pct']:.1f}%)"


def _artifact_size_section(experiment):
    if experiment.id not in (5, 6, 7, 8):
        return []
    label = "Representation sizes" if experiment.id == 5 else "Compression sizes" if experiment.id in (6, 7) else "Context sizes and recommendation position"
    lines = [f"## {label}", "", "| World | A tokens | B tokens | Reduction B vs A | A recommendation position | B recommendation position |", "|---|---:|---:|---:|---:|---:|"]
    for world in world_ids():
        a = artifact_metadata(experiment, world, "A")
        b = artifact_metadata(experiment, world, "B")
        reduction = round(100 * (a["approx_tokens"] - b["approx_tokens"]) / a["approx_tokens"], 1)
        lines.append(
            f"| {world} | {a['approx_tokens']} | {b['approx_tokens']} | {reduction:.1f}% | "
            f"{a.get('recommendation_position_fraction', 'n/a')} | {b.get('recommendation_position_fraction', 'n/a')} |"
        )
    lines.append("")
    return lines


def write_experiment_reports(rows, jsonl, experiment_value=None):
    if not rows:
        raise ValueError("cannot report an empty result file")
    experiment = get_experiment(experiment_value or rows[0]["experiment"])
    if any(row.get("experiment") != experiment.id for row in rows):
        raise ValueError("result file contains more than one experiment")
    path = Path(jsonl)
    summaries = summarize(rows)
    csv_path = path.with_suffix(".csv")
    fields = list(summaries[0])
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summaries)

    models = sorted({row["model"] for row in rows})
    temperatures = sorted({row.get("sampling", {}).get("requested_temperature", row.get("model_parameters", {}).get("temperature")) for row in rows}, key=str)
    lines = [
        f"# Experiment {experiment.id} — {experiment.title}", "", "## Question", "", experiment.research_question, "",
        "## Manipulation", "", f"The independent variable is **{experiment.independent_variable}**. Condition A is {experiment.condition_a}; condition B is {experiment.condition_b}. All other prompt components are held constant within each world.", "",
        "## Setup", "", f"- Model(s): {', '.join(models)}", f"- Worlds: {', '.join(sorted({row['world'] for row in rows}))}",
        f"- Calls: {len(rows)}", f"- Temperature requested: {', '.join(map(str, temperatures))}", "",
        "Repeated temperature-zero observations are low-variance repeats, not fully independent experimental units. The worlds are the more important source of variation.", "",
        "## Results", "",
    ]
    for model in models:
        if len(models) > 1:
            lines.extend([f"### {model}", ""])
        aggregates = [row for row in summaries if row["model"] == model and row["world"] == "ALL"]
        lines.extend(["| Condition | N | Correct | Preferred (Wilson 95%) | Alternative | Mixed | Invalid |", "|---|---:|---:|---:|---:|---:|---:|"])
        for row in aggregates:
            label = experiment.condition_label(row["condition"])
            preferred = f"{_format_count(row, 'preferred_path')} [{row['preferred_wilson_low']:.1f}, {row['preferred_wilson_high']:.1f}]"
            lines.append(f"| {row['condition']} — {label} | {row['n']} | {_format_count(row, 'world_correct')} | {preferred} | {_format_count(row, 'alternative_path')} | {_format_count(row, 'mixed_path')} | {_format_count(row, 'invalid_answer')} |")
        comparison = _comparison(rows, model)
        lines.extend(["", "## Effect" if len(models) == 1 else f"### Effect for {model}", "", f"Preferred-path difference (B − A): {comparison['difference_b_minus_a_pp']:+.2f} percentage points. Fisher's exact p = {comparison['fisher_p']}.", ""])

    lines.extend(_artifact_size_section(experiment))
    lines.extend(["## By world", "", "| Model | World | Condition | N | Correct | Preferred | Alternative | Mixed | Invalid |", "|---|---|---|---:|---:|---:|---:|---:|---:|"])
    for row in summaries:
        if row["world"] == "ALL":
            continue
        lines.append(f"| {row['model']} | {row['world']} | {row['condition']} | {row['n']} | {_format_count(row, 'world_correct')} | {_format_count(row, 'preferred_path')} | {_format_count(row, 'alternative_path')} | {_format_count(row, 'mixed_path')} | {_format_count(row, 'invalid_answer')} |")
    lines.extend([
        "", "## Interpretation", "",
        "Interpret the direct two-condition contrast together with its world-level pattern. A null aggregate remains informative and should not cause later experiments to be skipped.", "",
        "## Caveats", "",
        "Five fictional worlds limit generalization. Repeated deterministic calls may be correlated, provider routing can vary, and approximate artifact token counts use a character-based estimator while run rows retain provider-reported usage when available.", "",
    ])
    md_path = path.with_suffix(".md")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def _interpretation(experiment, comparison):
    significant = comparison["fisher_p"] is not None and comparison["fisher_p"] < 0.05
    diff = comparison["difference_b_minus_a_pp"]
    if experiment.id == 1:
        return "effect" if significant else "no detectable effect"
    if experiment.id in (2, 3, 4):
        return "effect" if significant else "no detectable effect"
    if experiment.id == 5:
        return "effect" if significant else "no detectable effect"
    if experiment.id in (6, 7):
        return "degraded behavior" if significant and diff < 0 else "preserved / no detectable degradation"
    if experiment.id == 8:
        return "effect" if significant else "no detectable effect"
    return "isolation helped" if significant and diff < 0 else "no detectable effect"


def write_chain_summary(results_directory, output=None):
    directory = Path(results_directory)
    rows = []
    seen = set()
    for path in sorted(directory.rglob("*.jsonl")):
        for row in read_jsonl(path):
            if not isinstance(row.get("experiment"), int) or not 1 <= row["experiment"] <= 9:
                continue
            identity = row.get("run_id") or (row["experiment"], row.get("model"), row.get("world"), row.get("condition"), row.get("trial"), str(path))
            if identity not in seen:
                rows.append(row)
                seen.add(identity)
    models = sorted({row["model"] for row in rows})
    lines = ["# Documentation experiment chain", ""]
    if not rows:
        lines.append("No numbered-experiment JSONL records were found.")
    for model in models:
        lines.extend([f"## Model: {model}", "", "| Exp | Question | A preferred | B preferred | Difference (B − A) |", "|---:|---|---:|---:|---:|"])
        interpretations = []
        labels = ["Recommendation presence", "Isolation", "Heading", "AI audience label", "Representation", "Semantic compression", "Stronger compression", "Context dilution", "Conflict correction"]
        for experiment in list_experiments():
            subset = [row for row in rows if row["model"] == model and row["experiment"] == experiment.id]
            if not subset:
                lines.append(f"| {experiment.id} | {experiment.title} | — | — | — |")
                interpretations.append(f"{labels[experiment.id - 1]}: not run")
                continue
            comparison = _comparison(subset, model)
            a_pct = _pct(comparison["a_preferred"], comparison["a_n"])
            b_pct = _pct(comparison["b_preferred"], comparison["b_n"])
            lines.append(f"| {experiment.id} | {experiment.title} | {a_pct:.1f}% | {b_pct:.1f}% | {comparison['difference_b_minus_a_pp']:+.1f} pp |")
            interpretations.append(f"{labels[experiment.id - 1]}: {_interpretation(experiment, comparison)}")
        lines.extend(["", "### Cumulative interpretation", ""] + [f"- {item}" for item in interpretations] + [""])
    output_path = Path(output) if output else directory / "chain-summary.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


# Historical compatibility alias for callers of the pilot API.
write_reports = write_experiment_reports
