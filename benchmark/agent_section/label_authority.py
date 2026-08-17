"""Quick isolated conflict experiment: generic heading versus For agents."""
from __future__ import annotations
import json, os, random, time, uuid
from datetime import datetime, timezone
from pathlib import Path

from . import PHASE, PROJECT, SYSTEM_PROMPT
from .project import PHASE_ROOT, artifact_path, estimate_tokens, sha256_text, tasks
from .scoring import score_response
from .runner import user_prompt
from ..env import load_dotenv
from ..openrouter import complete, response_text

ROOT = PHASE_ROOT / "follow-ups" / "label-authority"
DATA = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

def doc(task_id, condition):
    normal = artifact_path(task_id, "A").read_text(encoding="utf-8")
    if condition == "A": return normal
    heading = "## Operational guidance" if condition == "B" else "## For agents"
    block = f"{heading}\n\n{DATA['blocks'][task_id]}"
    head, tail = normal.split("\n---\n\n", 1)
    return head + "\n\n" + block + "\n\n---\n\n" + tail

def run(model, runs=1, seed=20260817):
    load_dotenv(); key=os.environ.get("OPENROUTER_API_KEY")
    if not key: raise RuntimeError("OPENROUTER_API_KEY is required")
    jobs=[(task,c,n) for task in tasks() for c in "ABC" for n in range(1,runs+1)]
    random.Random(seed).shuffle(jobs)
    output=ROOT / "results" / f"{model.replace('/','-')}-runs-{runs}.jsonl"; output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8") as stream:
      for task,condition,trial in jobs:
        documentation=doc(task.id,condition); prompt=user_prompt(documentation,task.prompt); started=time.perf_counter()
        response=complete(model,SYSTEM_PROMPT,prompt,key,temperature=0.0); raw=response_text(response); evaluation=score_response(task.id,raw)
        row={"run_id":str(uuid.uuid4()),"timestamp":datetime.now(timezone.utc).isoformat(),"phase":PHASE,"project":PROJECT,"experiment":"label-authority","model":model,"task":task.id,"trial":trial,"condition":condition,"documentation_sha256":sha256_text(documentation),"task_sha256":sha256_text(task.prompt),"prompt_tokens":response.get("usage",{}).get("prompt_tokens") or estimate_tokens(prompt),"raw_output":raw,"raw_response":response,"latency_ms":response.get("_latency_ms",round((time.perf_counter()-started)*1000,2)),**evaluation.as_dict()}
        stream.write(json.dumps(row,ensure_ascii=False)+"\n"); stream.flush()
    return output

def report(path):
    rows=[json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x]
    lines=["# Label-authority follow-up","","| Condition | Current/correct decisions | Fully correct responses |","| --- | ---: | ---: |"]
    for c in "ABC":
      group=[r for r in rows if r["condition"]==c]; total=sum(r["total_decisions"] for r in group); current=sum(r["current_correct_decisions"] for r in group); full=sum(r["fully_correct"] for r in group)
      lines.append(f"| {c} | {current/total:.1%} | {full/len(group):.1%} |")
    target=Path(path).with_suffix(".md"); target.write_text("\n".join(lines)+"\n",encoding="utf-8"); return target
