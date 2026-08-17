import csv
import json
from collections import defaultdict
from pathlib import Path

from .stats import fisher, wilson


def mean(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    return round(sum(values) / len(values), 2) if values else None


def pct(k, n):
    return round(100 * k / n, 2) if n else 0.0


def summarize(rows, keys=("model", "world", "condition")):
    groups = defaultdict(list)
    for row in rows: groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for group_key, group in sorted(groups.items()):
        n = len(group)
        output.append({**dict(zip(keys, group_key)), "n": n,
            "world_correct_pct": pct(sum(bool(r["world_correct"]) for r in group), n), "preferred_pct": pct(sum(bool(r["preferred_path"]) for r in group), n),
            "preferred_correct_pct": pct(sum(bool(r["preferred_path"]) for r in group), sum(bool(r["world_correct"]) for r in group)),
            "alternative_pct": pct(sum(bool(r["alternative_path"]) for r in group), n), "mixed_pct": pct(sum(bool(r["mixed_path"]) for r in group), n), "invalid_pct": pct(sum(bool(r["invalid_answer"]) for r in group), n),
            "mean_input_tokens": mean(group, "prompt_tokens"), "mean_output_tokens": mean(group, "completion_tokens"), "mean_latency_ms": mean(group, "latency_ms"), "mean_cost_usd": mean(group, "cost_usd")})
    return output


def aggregate(rows):
    return summarize(rows, keys=("model", "condition"))


def comparisons(rows):
    pairs = [("A", "E"), ("B", "E"), ("C", "E"), ("D", "E"), ("F", "E"), ("A", "F"), ("A", "D"), ("B", "C")]
    output = []
    for model in sorted({row["model"] for row in rows}):
        for world in sorted({row["world"] for row in rows}):
            for left, right in pairs:
                l = [r for r in rows if r["model"] == model and r["world"] == world and r["condition"] == left]
                r = [r for r in rows if r["model"] == model and r["world"] == world and r["condition"] == right]
                if not l or not r: continue
                lk = sum(bool(x["preferred_path"]) for x in l); rk = sum(bool(x["preferred_path"]) for x in r)
                output.append({"model": model, "world": world, "comparison": f"{left} vs {right}", "left_preferred": lk, "left_n": len(l), "right_preferred": rk, "right_n": len(r), "fisher_p": fisher(lk, len(l) - lk, rk, len(r) - rk)})
    return output


def write_reports(rows, jsonl):
    path = Path(jsonl); aggregate_rows = aggregate(rows)
    csv_path = path.with_suffix(".csv")
    fields = list(aggregate_rows[0]) if aggregate_rows else ["model"]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(aggregate_rows)
    md_path = path.with_suffix(".md")
    lines = ["# Fable benchmark report", "", "## Aggregate by model and condition", "", "| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    lines.extend("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |" for row in aggregate_rows)
    lines += ["", "## By world", "", "```json", json.dumps(summarize(rows), indent=2), "```", "", "## Pairwise comparisons", "", "```json", json.dumps(comparisons(rows), indent=2), "```"]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, md_path
