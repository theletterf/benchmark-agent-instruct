from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .chain import format_chain_inspection, run_chain, safe_model_name
from .experiments import CONDITIONS, artifact_metadata, experiment_as_dict, get_experiment, list_experiments, load_artifact, unified_diff, validate_all, validate_experiment
from .prompts import SYSTEM_PROMPT, task, user_prompt
from .reports import read_jsonl, write_chain_summary, write_experiment_reports
from .runner import run_calibration, run_experiment
from .worlds import world_ids
from .real_docs.cli import configure_parser as configure_real_docs_parser, handle as handle_real_docs
from .agent_section.cli import configure_parser as configure_agent_section_parser, handle as handle_agent_section


def _experiment_parser(subparsers):
    parser = subparsers.add_parser("experiment", help="inspect, validate, run, or report one numbered experiment")
    parser.add_argument("experiment")
    actions = parser.add_subparsers(dest="experiment_action", required=True)
    inspect = actions.add_parser("inspect")
    inspect.add_argument("--world", choices=world_ids(), default=world_ids()[0])
    diff = actions.add_parser("diff")
    diff.add_argument("--world", choices=world_ids(), default=world_ids()[0])
    actions.add_parser("validate")
    run = actions.add_parser("run")
    run.add_argument("--model", required=True)
    run.add_argument("--runs", type=int, default=3)
    run.add_argument("--smoke", action="store_true")
    run.add_argument("--world", choices=world_ids())
    run.add_argument("--worlds", nargs="+", choices=world_ids())
    run.add_argument("--output", type=Path)
    run.add_argument("--seed", type=int)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--allow-invalid", action="store_true", help="explicitly override manipulation validation failures")
    report = actions.add_parser("report")
    report.add_argument("jsonl", type=Path)


def _chain_parser(subparsers):
    parser = subparsers.add_parser("chain", help="inspect, execute, or summarize the conceptual chain")
    actions = parser.add_subparsers(dest="chain_action", required=True)
    for name in ("inspect", "run"):
        current = actions.add_parser(name)
        current.add_argument("--model", required=True)
        current.add_argument("--runs", type=int, default=3)
        current.add_argument("--from", dest="start", type=int, default=1)
        current.add_argument("--to", dest="end", type=int, default=9)
        if name == "run":
            current.add_argument("--execute", action="store_true", help="required acknowledgement for paid API calls")
            current.add_argument("--results-dir", type=Path, default=Path("results/chain"))
            current.add_argument("--seed", type=int)
            current.add_argument("--allow-invalid", action="store_true")
    summary = actions.add_parser("summary")
    summary.add_argument("results", type=Path)
    summary.add_argument("--output", type=Path)


def build_parser():
    parser = argparse.ArgumentParser(prog="python -m benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    experiments = sub.add_parser("experiments")
    experiments.add_subparsers(dest="experiments_action", required=True).add_parser("list")
    _experiment_parser(sub)
    _chain_parser(sub)
    sub.add_parser("validate", help="validate all nine frozen experiments")
    calibrate = sub.add_parser("calibrate", help="diagnostic neutral-condition run (5 worlds × runs)")
    calibrate.add_argument("--model", required=True)
    calibrate.add_argument("--runs", type=int, default=3)
    calibrate.add_argument("--output", type=Path)
    calibrate.add_argument("--seed", type=int)
    real_docs = sub.add_parser("real-docs", help="Phase 2 experiments over frozen real documentation")
    configure_real_docs_parser(real_docs)
    agent_section = sub.add_parser("agent-section", help="Phase 3 normal docs vs the same docs plus For agents")
    configure_agent_section_parser(agent_section)
    return parser


def _positive_runs(value):
    if value < 1:
        raise SystemExit("--runs must be at least 1")


def _print_experiment_inspect(experiment, world_id):
    print(json.dumps(experiment_as_dict(experiment), indent=2))
    print(f"\nWorld: {world_id} (use --world to inspect another frozen world)")
    print(f"System SHA-256: {__import__('hashlib').sha256(SYSTEM_PROMPT.encode()).hexdigest()}")
    print(f"Task: {task(experiment, world_id)}")
    for condition in CONDITIONS:
        print(f"\n===== Condition {condition}: {experiment.condition_label(condition)} =====")
        print(json.dumps(artifact_metadata(experiment, world_id, condition), indent=2))
        print(load_artifact(experiment, world_id, condition), end="")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "agent-section":
        return handle_agent_section(args)
    if args.command == "real-docs":
        return handle_real_docs(args)
    if args.command == "experiments":
        for experiment in list_experiments():
            print(f"{experiment.id}  {experiment.name}")
        return 0
    if args.command == "validate":
        failures = False
        for experiment in list_experiments():
            errors = validate_experiment(experiment.id)
            if errors:
                failures = True
                print(f"{experiment.id} {experiment.name}: FAILED")
                print("\n".join(f"  - {error}" for error in errors))
            else:
                print(f"{experiment.id} {experiment.name}: valid (5 worlds × 2 conditions)")
        return 1 if failures else 0
    if args.command == "experiment":
        try:
            experiment = get_experiment(args.experiment)
        except KeyError as exc:
            raise SystemExit(str(exc)) from exc
        if args.experiment_action == "inspect":
            _print_experiment_inspect(experiment, args.world)
            return 0
        if args.experiment_action == "diff":
            print(unified_diff(experiment.id, args.world), end="")
            return 0
        if args.experiment_action == "validate":
            errors = validate_experiment(experiment.id)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            print(f"Experiment {experiment.id} — {experiment.title}: valid across 5 worlds × 2 conditions")
            return 0
        if args.experiment_action == "report":
            rows = read_jsonl(args.jsonl)
            csv_path, md_path = write_experiment_reports(rows, args.jsonl, experiment.id)
            print(f"wrote {csv_path}\nwrote {md_path}")
            return 0
        _positive_runs(args.runs)
        errors = validate_experiment(experiment.id)
        if errors and not args.allow_invalid:
            print("Validation failed; no API calls were made:\n" + "\n".join(errors), file=sys.stderr)
            return 1
        selected_worlds = [world_ids()[0]] if args.smoke else [args.world] if args.world else args.worlds or world_ids()
        repetitions = 2 if args.smoke else args.runs
        output = args.output or Path("results") / f"{experiment.id:02d}-{experiment.name}-{safe_model_name(args.model)}.jsonl"
        calls = len(selected_worlds) * 2 * repetitions
        print(f"Executing {calls} OpenRouter calls -> {output}")
        run_experiment(experiment.id, args.model, selected_worlds, repetitions, output, seed=args.seed, resume=args.resume)
        return 0
    if args.command == "chain":
        if args.chain_action == "summary":
            print(f"wrote {write_chain_summary(args.results, args.output)}")
            return 0
        _positive_runs(args.runs)
        try:
            inspection = format_chain_inspection(args.model, args.runs, args.start, args.end)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print(inspection)
        if args.chain_action == "inspect":
            print("\nInspection only: no API calls were made.")
            return 0
        if not args.execute:
            print("\nRefusing to call OpenRouter without --execute.", file=sys.stderr)
            return 2
        outputs = run_chain(args.model, args.runs, args.start, args.end, args.results_dir, args.seed, args.allow_invalid)
        print("\nCompleted/resumed outputs:\n" + "\n".join(str(path) for path in outputs))
        return 0
    _positive_runs(args.runs)
    output = args.output or Path("results") / f"calibration-{safe_model_name(args.model)}.jsonl"
    print(f"Executing {len(world_ids()) * args.runs} diagnostic OpenRouter calls -> {output}")
    run_calibration(args.model, args.runs, output, args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
