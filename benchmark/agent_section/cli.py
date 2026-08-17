"""CLI surface for Phase 3."""
from __future__ import annotations

import json
from pathlib import Path

from .artifacts import token_metrics, validate_all
from .attention_check import ROOT as ATTENTION_ROOT, attention_plan, build as build_attention_check, default_output as attention_default_output, run_attention_check, validate as validate_attention_check, write_attention_report
from .project import artifact_path, decisions, diff_path, source_manifest, tasks
from .reports import write_report
from .runner import default_output, plan, run_experiment


def configure_parser(parser):
    actions = parser.add_subparsers(dest="agent_section_action", required=True)
    for name in ("inspect", "diff", "validate"):
        current = actions.add_parser(name)
        current.add_argument("project", choices=["opentelemetry"])
    run = actions.add_parser("run")
    run.add_argument("project", choices=["opentelemetry"])
    run.add_argument("--model", required=True)
    run.add_argument("--runs", type=int, default=3)
    run.add_argument("--smoke", action="store_true")
    run.add_argument("--dry-run", action="store_true", help="validate and print the call plan without network calls")
    run.add_argument("--output", type=Path)
    run.add_argument("--seed", type=int)
    run.add_argument("--temperature", type=float, default=0.0)
    report = actions.add_parser("report")
    report.add_argument("jsonl", type=Path)
    report.add_argument("--output", type=Path)
    attention = actions.add_parser("attention-check", help="inspect or validate the separate non-production conflict diagnostic")
    attention.add_argument("action", choices=["build", "validate", "diff", "run", "report"])
    attention.add_argument("project", choices=["opentelemetry"])
    attention.add_argument("--model")
    attention.add_argument("--runs", type=int, default=3)
    attention.add_argument("--smoke", action="store_true")
    attention.add_argument("--dry-run", action="store_true")
    attention.add_argument("--output", type=Path)
    attention.add_argument("--seed", type=int)
    attention.add_argument("--temperature", type=float, default=0.0)
    attention.add_argument("--jsonl", type=Path)


def handle(args):
    action = args.agent_section_action
    if action == "inspect":
        print(json.dumps({
            "phase": 3, "project": args.project,
            "sources": source_manifest()["sources"],
            "tasks": [{
                "id": task.id, "title": task.title, "prompt": task.prompt,
                "scorable_decisions": len(decisions(task.id)),
                "token_metrics": token_metrics(task.id),
                "for_agents": task.agent_section,
            } for task in tasks()],
        }, indent=2, ensure_ascii=False))
        return 0
    if action == "diff":
        for task in tasks():
            print(diff_path(task.id).read_text(encoding="utf-8"), end="")
        return 0
    if action == "validate":
        errors = validate_all()
        if errors:
            print("\n".join(f"- {error}" for error in errors))
            return 1
        print("Phase 3 opentelemetry: valid (5 tasks × 2 conditions; treatment differs only by one supported For agents block)")
        return 0
    if action == "report":
        path = write_report(args.jsonl, args.output)
        print(f"wrote {path}")
        return 0
    if action == "attention-check":
        if args.action == "build":
            build_attention_check()
            print(f"wrote {ATTENTION_ROOT / 'artifacts'}")
            return 0
        if args.action == "diff":
            for task in tasks():
                print((ATTENTION_ROOT / "diffs" / f"{task.id}.diff").read_text(encoding="utf-8"), end="")
            return 0
        if args.action == "report":
            if not args.jsonl:
                raise SystemExit("attention-check report requires --jsonl")
            print(f"wrote {write_attention_report(args.jsonl, args.output)}")
            return 0
        if args.action == "run":
            if not args.model:
                raise SystemExit("attention-check run requires --model")
            if args.runs < 1:
                raise SystemExit("--runs must be at least 1")
            errors = validate_attention_check()
            if errors:
                print("Validation failed; no API calls were made:\n" + "\n".join(errors))
                return 1
            jobs = attention_plan(args.smoke, args.runs, args.seed)
            output = args.output or attention_default_output(args.model, args.smoke, args.runs)
            if args.dry_run:
                print(f"DRY RUN: {len(jobs)} calls -> {output}\nNo API calls were made.")
                return 0
            print(f"Executing {len(jobs)} OpenRouter calls -> {output}")
            print(run_attention_check(args.model, args.runs, args.smoke, output, args.seed, args.temperature))
            return 0
        errors = validate_attention_check()
        if errors:
            print("\n".join(f"- {error}" for error in errors))
            return 1
        print("Phase 3 attention-check follow-up: valid; H differs from B only by its marked non-production counterfactual block")
        return 0
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")
    errors = validate_all()
    if errors:
        print("Validation failed; no API calls were made:\n" + "\n".join(errors))
        return 1
    jobs = plan(smoke=args.smoke, runs=args.runs, seed=args.seed)
    output = args.output or default_output(args.model, args.smoke, args.runs)
    if args.dry_run:
        print(f"DRY RUN: {len(jobs)} calls -> {output}")
        for task, condition, trial in jobs:
            print(f"{task.id}\tcondition={condition}\ttrial={trial}")
        print("No API calls were made.")
        return 0
    print(f"Executing {len(jobs)} OpenRouter calls -> {output}")
    print(run_experiment(args.model, args.runs, args.smoke, output, args.seed, args.temperature))
    return 0
