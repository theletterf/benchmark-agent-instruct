from __future__ import annotations

from dataclasses import asdict, dataclass
import re

from .project import DECISIONS

@dataclass(frozen=True)
class Evaluation:
    decisions: list[dict]
    current_decisions: int
    historical_decisions: int
    invalid_decisions: int
    current_rate: float
    fully_current: bool
    def as_dict(self): return asdict(self)

def score_response(text):
    code = re.search(r"```(?:python)?\s*(.*?)```", text, re.S | re.I)
    code = code.group(1) if code else text
    decisions = []
    for name, current, historical in DECISIONS:
        c = bool(re.search(re.escape(current), code))
        h = bool(re.search(re.escape(historical), code))
        classification = "mixed" if c and h else "current" if c else "historical" if h else "invalid"
        decisions.append({"name": name, "classification": classification})
    current = sum(item["classification"] == "current" for item in decisions)
    historical = sum(item["classification"] == "historical" for item in decisions)
    invalid = sum(item["classification"] == "invalid" for item in decisions)
    return Evaluation(decisions, current, historical, invalid, current / len(decisions), current == len(decisions))
