"""Deterministic decision-level scoring for OpenTelemetry responses."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class DecisionEvaluation:
    name: str
    value: str | None
    classification: str
    name_current: bool
    normative_correct: bool
    condition_correct: bool
    version_context_correct: bool
    requirement: str
    condition: str | None


@dataclass(frozen=True)
class OtelEvaluation:
    decisions: tuple[DecisionEvaluation, ...]
    current_decisions: int
    historical_decisions: int
    mixed_response: bool
    fully_current: bool
    current_decision_rate: float

    def as_dict(self):
        payload = asdict(self)
        payload["decisions"] = [asdict(item) for item in self.decisions]
        return payload


def _find(text, values):
    lowered = text.lower()
    for value in values:
        # Attribute names are dotted identifiers.  A historical prefix such
        # as ``db.system`` must not be detected inside ``db.system.name``.
        pattern = rf"(?<![A-Za-z0-9_.]){re.escape(value.lower())}(?![A-Za-z0-9_.])"
        if re.search(pattern, lowered):
            return value
    return None


def answer_mapping(response):
    """Return the requested mapping rather than explanatory prose.

    Tasks ask for a compact YAML mapping.  A model may still append prose that
    quotes historical terminology. Counting that prose would turn a current
    requested answer into an artificial mixed response, so score the first
    fenced YAML block when present.
    """
    match = re.search(r"```(?:yaml|yml)?\s*\n?(.*?)```", response, flags=re.IGNORECASE | re.DOTALL)
    mapping = match.group(1).strip() if match else response
    # The prompt permits a compact YAML mapping.  Both ``service.name: x``
    # and the equivalent nested YAML mapping are valid representations.
    return re.sub(r"(?mi)^service\s*:\s*\n\s+name\s*:", "service.name:", mapping)


def score_response(task, response):
    """Classify each pinned decision without consulting model knowledge.

    A decision that contains both current and historical forms is mixed. Missing
    forms are unclassified. Normative/condition fields are explicitly retained
    so future tasks that require requirement-level output can use the same
    schema; for these compact generation tasks the current pinned form is the
    specified norm under the task's stated condition.
    """
    response = answer_mapping(response)
    evaluated = []
    for decision in task.decisions:
        current = _find(response, decision.current)
        historical = _find(response, decision.historical)
        if current and historical:
            classification, value = "mixed", current
        elif current:
            classification, value = "current", current
        elif historical:
            classification, value = "historical", historical
        else:
            classification, value = "unclassified", None
        is_current = classification == "current"
        evaluated.append(DecisionEvaluation(
            name=decision.id, value=value, classification=classification,
            name_current=is_current,
            normative_correct=is_current,
            condition_correct=is_current,
            version_context_correct=is_current,
            requirement=decision.requirement, condition=decision.condition,
        ))
    current_count = sum(item.classification == "current" for item in evaluated)
    historical_count = sum(item.classification == "historical" for item in evaluated)
    mixed_response = any(item.classification == "mixed" for item in evaluated) or (current_count > 0 and historical_count > 0)
    return OtelEvaluation(
        decisions=tuple(evaluated), current_decisions=current_count,
        historical_decisions=historical_count, mixed_response=mixed_response,
        fully_current=bool(evaluated) and current_count == len(evaluated),
        current_decision_rate=current_count / len(evaluated) if evaluated else 0.0,
    )
