from __future__ import annotations
import argparse
from pathlib import Path
from . import CONDITIONS
from .project import validate
from .runner import build, run, read

def configure_parser(parser):
    actions = parser.add_subparsers(dest="pinecone_label_action", required=True)
    for action in ("build", "validate", "diff"):
        actions.add_parser(action)
    runner = actions.add_parser("run")
    runner.add_argument("--model", required=True); runner.add_argument("--runs", type=int, default=3); runner.add_argument("--seed", type=int); runner.add_argument("--temperature", type=float, default=0.0); runner.add_argument("--dry-run", action="store_true"); runner.add_argument("--output", type=Path)

def handle(args):
    if args.pinecone_label_action == "build":
        build(); print("wrote frozen Pinecone label artifacts"); return 0
    errors = validate()
    if errors:
        print("Validation failed:\n" + "\n".join(f"- {error}" for error in errors)); return 1
    if args.pinecone_label_action == "validate": print("Pinecone label study: valid"); return 0
    if args.pinecone_label_action == "diff":
        import difflib
        from .project import artifact_path
        for left, right in (("N", "G"), ("G", "AI")):
            print("".join(difflib.unified_diff(artifact_path(left).read_text().splitlines(True), artifact_path(right).read_text().splitlines(True), fromfile=artifact_path(left).name, tofile=artifact_path(right).name)), end="")
        return 0
    if args.runs < 1: raise SystemExit("--runs must be at least 1")
    calls = args.runs * len(CONDITIONS)
    if args.dry_run: print(f"DRY RUN: {calls} OpenRouter calls; no API calls were made."); return 0
    print(f"Executing {calls} OpenRouter calls")
    print(run(args.model, args.runs, args.output, args.seed, args.temperature)); return 0
