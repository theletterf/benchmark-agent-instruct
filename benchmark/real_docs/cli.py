from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import EXPERIMENTS, artifact_metadata, experiment_dict, get_experiment, load_artifact, unified_diff, validate_all, validate_experiment
from .chain import format_inspection, require_headroom, run_chain
from .projects import sqlalchemy as project
from .projects import opentelemetry as otel_project
from .otel_reports import write_calibration_report as write_otel_calibration_report, write_candidate_report, write_headroom_report
from .otel_runner import calibration_output_path as otel_calibration_output_path, run_calibration as run_otel_calibration, rescore_calibration
from .reports import write_calibration_report, write_cross_phase_report, write_experiment_report, write_phase2_summary
from .runner import calibration_output_path, read_jsonl, run_calibration, run_experiment


def configure_parser(parser):
    commands = parser.add_subparsers(dest="real_command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", choices=[project.PROJECT, otel_project.PROJECT])
    validate = commands.add_parser("validate")
    validate.add_argument("project", choices=[project.PROJECT, otel_project.PROJECT])
    candidates = commands.add_parser("candidates")
    candidates.add_argument("project", choices=[otel_project.PROJECT])
    calibrate = commands.add_parser("calibrate")
    calibrate.add_argument("project", choices=[project.PROJECT, otel_project.PROJECT])
    calibrate.add_argument("--stage", choices=["prior", "docs"])
    calibrate.add_argument("--model", required=True)
    calibrate.add_argument("--runs", type=int, default=2)
    calibrate.add_argument("--temperature", type=float, default=0.0)
    calibrate.add_argument("--seed", type=int)
    calibrate.add_argument("--output", type=Path)
    calibrate.add_argument("--dry-run", action="store_true", help="show planned calls without contacting OpenRouter")

    headroom = commands.add_parser("headroom")
    headroom.add_argument("project", choices=[otel_project.PROJECT])
    headroom.add_argument("--model", required=True)
    headroom.add_argument("--output", type=Path)

    rescore = commands.add_parser("rescore")
    rescore.add_argument("project", choices=[otel_project.PROJECT])
    rescore.add_argument("jsonl", type=Path)
    rescore.add_argument("--output", type=Path)

    experiments = commands.add_parser("experiments")
    experiments.add_subparsers(dest="real_experiments_action", required=True).add_parser("list")

    experiment = commands.add_parser("experiment")
    experiment.add_argument("experiment")
    actions = experiment.add_subparsers(dest="real_experiment_action", required=True)
    for action in ("inspect", "diff"):
        current = actions.add_parser(action)
        current.add_argument("--task", choices=project.task_ids(), default=project.task_ids()[0])
    actions.add_parser("validate")
    run = actions.add_parser("run")
    run.add_argument("--project", choices=[project.PROJECT], default=project.PROJECT)
    run.add_argument("--model", required=True)
    run.add_argument("--runs", type=int, default=3)
    run.add_argument("--temperature", type=float, default=0.0)
    run.add_argument("--smoke", action="store_true")
    run.add_argument("--task", choices=project.task_ids())
    run.add_argument("--output", type=Path)
    run.add_argument("--seed", type=int)
    run.add_argument("--resume", action="store_true")
    report = actions.add_parser("report")
    report.add_argument("jsonl", type=Path)

    chain = commands.add_parser("chain")
    chain_actions = chain.add_subparsers(dest="real_chain_action", required=True)
    for action in ("inspect", "run"):
        current = chain_actions.add_parser(action)
        current.add_argument("project", choices=[project.PROJECT])
        current.add_argument("--model", required=True)
        current.add_argument("--runs", type=int, default=3)
        current.add_argument("--temperature", type=float, default=0.0)
        if action == "run":
            current.add_argument("--execute", action="store_true")
            current.add_argument("--seed", type=int)
    summary = chain_actions.add_parser("summary")
    summary.add_argument("results", nargs="?", type=Path)
    summary.add_argument("--output", type=Path)

    compare = commands.add_parser("compare")
    compare.add_argument("phase1_results", nargs="?", type=Path, default=Path("results"))
    compare.add_argument("--phase2-results", type=Path)
    compare.add_argument("--output", type=Path)


def _positive(value):
    if value < 1:
        raise SystemExit("--runs must be at least 1")


def _inspect_project():
    manifest = project.source_manifest()
    print(json.dumps({"phase": 2, "project": project.PROJECT, "version": project.VERSION, "sources": manifest["sources"],
                      "tasks": [{"id": task.id, "title": task.title, "signature": task.signature, "current_patterns": task.current_patterns, "legacy_patterns": task.legacy_patterns} for task in project.tasks()]}, indent=2))


def _inspect_otel_project():
    manifest = otel_project.source_manifest()
    print(json.dumps({"phase": 2, "project": otel_project.PROJECT, "version": otel_project.VERSION, "sources": manifest["sources"],
                      "candidate_status": "calibration-gated; no nine-experiment artifacts have been generated",
                      "tasks": [{"id": task.id, "title": task.title, "decisions": [decision.id for decision in task.decisions]} for task in otel_project.tasks()]}, indent=2))


def handle(args):
    if args.real_command == "inspect":
        if args.project == otel_project.PROJECT:
            _inspect_otel_project()
        else:
            _inspect_project()
        return 0
    if args.real_command == "candidates":
        print(f"wrote {write_candidate_report()}")
        return 0
    if args.real_command == "validate":
        if args.project == otel_project.PROJECT:
            errors = otel_project.validate_sources()
            known_sources = {item["id"] for item in otel_project.source_manifest()["sources"]}
            for task in otel_project.tasks():
                for decision in task.decisions:
                    if not decision.current or not decision.historical:
                        errors.append(f"{task.id}:{decision.id} lacks a current or historical form")
                    if decision.source_id not in known_sources:
                        errors.append(f"{task.id}:{decision.id} points to unknown source {decision.source_id}")
            print(f"sources and decision manifests: {'valid' if not errors else 'FAILED'}")
            if errors:
                print("\n".join(f"  - {error}" for error in errors))
                return 1
            print(f"candidate tasks: valid ({len(otel_project.tasks())} tasks × {sum(len(task.decisions) for task in otel_project.tasks())} decisions)")
            return 0
        failures = False
        source_errors = project.validate_sources()
        print(f"sources: {'valid' if not source_errors else 'FAILED'}")
        if source_errors:
            failures = True; print("\n".join(f"  - {error}" for error in source_errors))
        for experiment in EXPERIMENTS:
            errors = validate_experiment(experiment.id)
            print(f"{experiment.id} {experiment.name}: {'valid' if not errors else 'FAILED'}")
            if errors:
                failures = True; print("\n".join(f"  - {error}" for error in errors))
        return 1 if failures else 0
    if args.real_command == "calibrate":
        _positive(args.runs)
        if args.project == otel_project.PROJECT:
            if not args.stage:
                raise SystemExit("OpenTelemetry calibration requires --stage prior or --stage docs")
            output = args.output or otel_calibration_output_path(args.model, args.stage, args.runs)
            calls = len(otel_project.tasks()) * args.runs
            label = "task-only" if args.stage == "prior" else "official-documentation"
            print(f"Executing {calls} OpenRouter {label} calibration calls -> {output}")
            if args.dry_run:
                print("Dry run: no API calls were made.")
                return 0
            path = run_otel_calibration(args.model, args.stage, args.runs, output, args.seed, args.temperature)
            csv_path, md_path = write_otel_calibration_report(__import__("benchmark.real_docs.otel_runner", fromlist=["read_jsonl"]).read_jsonl(path), path)
            print(f"wrote {csv_path}\nwrote {md_path}")
            return 0
        if args.stage:
            raise SystemExit("--stage is only valid for the OpenTelemetry candidate")
        output = args.output or calibration_output_path(args.model, args.runs)
        print(f"Executing {len(project.tasks()) * args.runs} task-only OpenRouter calls -> {output}")
        if args.dry_run:
            print("Dry run: no API calls were made.")
            return 0
        path = run_calibration(args.model, args.runs, output, args.seed, args.temperature)
        csv_path, md_path = write_calibration_report(read_jsonl(path), path)
        print(f"wrote {csv_path}\nwrote {md_path}")
        return 0
    if args.real_command == "headroom":
        try:
            path, assessment = write_headroom_report(args.model, args.output)
        except RuntimeError as exc:
            print(f"OpenTelemetry headroom assessment blocked: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {path}")
        print(f"Overall suitability: {'GOOD' if assessment['suitable'] else 'INSUFFICIENT'}")
        return 0
    if args.real_command == "rescore":
        path = rescore_calibration(args.jsonl, args.output)
        csv_path, md_path = write_otel_calibration_report(__import__("benchmark.real_docs.otel_runner", fromlist=["read_jsonl"]).read_jsonl(path), path)
        print(f"wrote {path}\nwrote {csv_path}\nwrote {md_path}")
        return 0
    if args.real_command == "experiments":
        for experiment in EXPERIMENTS:
            print(f"{experiment.id}  {experiment.name}")
        return 0
    if args.real_command == "experiment":
        try: experiment = get_experiment(args.experiment)
        except KeyError as exc: raise SystemExit(f"unknown Phase 2 experiment: {args.experiment}") from exc
        action = args.real_experiment_action
        if action == "inspect":
            task = project.get_task(args.task)
            print(json.dumps(experiment_dict(experiment), indent=2))
            print(f"\nTask: {task.id}\n{project.task_prompt(task)}")
            for condition in ("A", "B"):
                print(f"\n===== {condition}: {experiment.condition_label(condition)} =====")
                print(json.dumps(artifact_metadata(experiment, task.id, condition), indent=2))
                print(load_artifact(experiment, task.id, condition), end="")
            return 0
        if action == "diff":
            print(unified_diff(experiment.id, args.task), end=""); return 0
        if action == "validate":
            errors = validate_experiment(experiment.id)
            if errors:
                print("\n".join(errors), file=sys.stderr); return 1
            print(f"Phase 2 Experiment {experiment.id} — {experiment.title}: valid across 5 tasks × 2 conditions")
            return 0
        if action == "report":
            paths = write_experiment_report(read_jsonl(args.jsonl), args.jsonl, experiment.id)
            print("\n".join(f"wrote {path}" for path in paths)); return 0
        _positive(args.runs)
        try:
            require_headroom(args.model)
        except RuntimeError as exc:
            print(f"Phase 2 run blocked: {exc}", file=sys.stderr)
            return 1
        task_ids = project.task_ids()[:2] if args.smoke else [args.task] if args.task else project.task_ids()
        repetitions = 1 if args.smoke else args.runs
        calls = len(task_ids) * 2 * repetitions
        print(f"Executing {calls} Phase 2 OpenRouter calls")
        path = run_experiment(experiment.id, args.model, task_ids, repetitions, args.output, args.seed, args.resume, args.temperature)
        print(f"wrote {path}"); return 0
    if args.real_command == "chain":
        if args.real_chain_action == "summary":
            print(f"wrote {write_phase2_summary(args.results, args.output)}"); return 0
        _positive(args.runs)
        print(format_inspection(args.model, args.runs))
        if args.real_chain_action == "inspect":
            print("\nInspection only: no API calls were made."); return 0
        if not args.execute:
            print("\nRefusing to call OpenRouter without --execute.", file=sys.stderr); return 2
        try:
            outputs = run_chain(args.model, args.runs, args.seed, args.temperature)
        except RuntimeError as exc:
            print(f"Phase 2 chain blocked: {exc}", file=sys.stderr)
            return 1
        print("\nCompleted/resumed outputs:\n" + "\n".join(str(path) for path in outputs)); return 0
    output = write_cross_phase_report(args.phase1_results, args.phase2_results, args.output)
    print(f"wrote {output}"); return 0
