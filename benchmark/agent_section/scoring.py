"""Deterministic decision-level JSON scoring; no LLM judge."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re
from typing import Any

from .project import decisions


@dataclass(frozen=True)
class DecisionScore:
    id: str
    classification: str
    observed: Any


@dataclass(frozen=True)
class Evaluation:
    decisions: tuple[DecisionScore, ...]
    current_correct_decisions: int
    historical_decisions: int
    invalid_decisions: int
    mixed_decisions: int
    total_decisions: int
    current_correct_rate: float
    fully_correct: bool
    mixed_current_historical: bool

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["decisions"] = [asdict(item) for item in self.decisions]
        return result


def parse_json_response(response: str) -> Any:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", response, flags=re.IGNORECASE | re.DOTALL)
    candidate = fenced.group(1).strip() if fenced else response.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", candidate):
            try:
                value, _ = decoder.raw_decode(candidate[match.start():])
                return value
            except json.JSONDecodeError:
                continue
    return None


def _at_path(value: Any, path: list[str]) -> Any:
    current = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.strip().casefold() == right.strip().casefold()
    if isinstance(left, list) and isinstance(right, list):
        return {_norm(item) for item in left} == {_norm(item) for item in right}
    return left == right or str(left).strip().casefold() == str(right).strip().casefold()


def _norm(value: Any) -> str:
    return str(value).strip().casefold()


def _one_of(value: Any, candidates: list[Any]) -> bool:
    return any(_equal(value, candidate) for candidate in candidates)


def _score_decision(payload: Any, decision: dict[str, Any]) -> DecisionScore:
    if not isinstance(payload, dict):
        return DecisionScore(decision["id"], "invalid", None)
    container = _at_path(payload, decision["path"])
    if decision["kind"] == "scalar":
        if _one_of(container, decision.get("current", [])):
            classification = "current"
        elif _one_of(container, decision.get("historical", [])):
            classification = "historical"
        else:
            classification = "invalid"
        return DecisionScore(decision["id"], classification, container)
    if decision["kind"] != "mapping_key" or not isinstance(container, dict):
        return DecisionScore(decision["id"], "invalid", container)
    current = [(key, container[key]) for key in decision.get("current_keys", []) if key in container]
    historical = [(key, container[key]) for key in decision.get("historical_keys", []) if key in container]
    expected = decision.get("expected", [])
    current_valid = any(_one_of(value, expected) for _, value in current)
    historical_valid = any(_one_of(value, expected) for _, value in historical)
    if current and historical:
        classification = "mixed" if current_valid or historical_valid else "invalid"
    elif current_valid:
        classification = "current"
    elif historical_valid:
        classification = "historical"
    else:
        classification = "invalid"
    return DecisionScore(decision["id"], classification, {key: value for key, value in current + historical} or None)


def score_response(task_id: str, response: str) -> Evaluation:
    payload = parse_json_response(response)
    scored = tuple(_score_decision(payload, decision) for decision in decisions(task_id))
    current = sum(item.classification == "current" for item in scored)
    historical = sum(item.classification == "historical" for item in scored)
    invalid = sum(item.classification == "invalid" for item in scored)
    mixed = sum(item.classification == "mixed" for item in scored)
    total = len(scored)
    mixed_response = mixed > 0 or (current > 0 and historical > 0)
    return Evaluation(
        decisions=scored, current_correct_decisions=current,
        historical_decisions=historical, invalid_decisions=invalid,
        mixed_decisions=mixed, total_decisions=total,
        current_correct_rate=current / total if total else 0.0,
        fully_correct=bool(total) and current == total,
        mixed_current_historical=mixed_response,
    )
