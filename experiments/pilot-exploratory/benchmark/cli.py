import argparse
import json
import sys
from pathlib import Path

from .artifacts import CONDITIONS, build_all, normalized_a_f_diff
from .prompts import SYSTEM_PROMPT, documentation, task, user_prompt
from .reports import write_reports
from .runner import run
from .worlds import all_worlds, world_ids


def validate():
    build_all()
    errors = []
    for world in all_worlds():
        if len(world["path_a"]["steps"]) != 3 or len(world["path_b"]["steps"]) != 3: errors.append(f"{world['id']}: paths must have three steps")
        for condition in CONDITIONS:
            text = documentation(world["id"], condition)
            if not text: errors.append(f"{world['id']} {condition}: empty artifact")
            for step in world["path_a"]["steps"] + world["path_b"]["steps"]:
                if step["id"].replace("_", " ") not in text.lower(): errors.append(f"{world['id']} {condition}: missing {step['id']}")
        if not normalized_a_f_diff(world["id"]): errors.append(f"{world['id']}: A/F differ beyond heading framing")
    if errors: raise SystemExit("\n".join(errors))
    print(f"validated {len(world_ids())} worlds × {len(CONDITIONS)} conditions")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    inspect = sub.add_parser("inspect"); inspect.add_argument("--world", required=True, choices=world_ids()); inspect.add_argument("--condition", required=True, choices=CONDITIONS)
    run_parser = sub.add_parser("run"); run_parser.add_argument("--models", nargs="+", required=True); run_parser.add_argument("--worlds", nargs="+", default=world_ids()); run_parser.add_argument("--world", dest="one_world"); run_parser.add_argument("--conditions", nargs="+", default=list(CONDITIONS)); run_parser.add_argument("--runs", type=int, default=20); run_parser.add_argument("--output", type=Path, default=Path("results/experiment.jsonl")); run_parser.add_argument("--seed", type=int); run_parser.add_argument("--resume", action="store_true")
    report = sub.add_parser("report"); report.add_argument("jsonl", type=Path)
    args = parser.parse_args(argv)
    if args.command == "validate": validate(); return 0
    if args.command == "inspect":
        print("SYSTEM:\n" + SYSTEM_PROMPT); print("\nUSER:\n" + user_prompt(args.world, args.condition)); return 0
    if args.command == "report":
        rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]; csv_path, md_path = write_reports(rows, args.jsonl); print(f"wrote {csv_path}\nwrote {md_path}"); return 0
    build_all()
    selected_worlds = [args.one_world] if args.one_world else args.worlds
    print(f"Running {len(args.models) * len(selected_worlds) * len(args.conditions) * args.runs} independent trials -> {args.output}")
    run(args.models, selected_worlds, args.conditions, args.runs, args.output, args.seed, args.resume); return 0


if __name__ == "__main__": sys.exit(main())
