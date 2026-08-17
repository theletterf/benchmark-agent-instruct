from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TaskSpec:
    id: str
    title: str
    function_name: str
    signature: str
    behavior: tuple[str, ...]
    source_ids: tuple[str, ...]
    official_excerpt: str
    source_assertions: tuple[str, ...]
    recommendation: str
    current_reference: str
    legacy_reference: str
    current_patterns: tuple[str, ...]
    legacy_patterns: tuple[str, ...]

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class RealExperiment:
    id: int
    name: str
    title: str
    research_question: str
    independent_variable: str
    condition_a: str
    condition_b: str
    default_runs: int = 3

    def condition_label(self, condition):
        return self.condition_a if condition == "A" else self.condition_b


@dataclass
class CodeEvaluation:
    syntax_success: bool
    runtime_success: bool
    functional_correct: bool
    api_classification: str
    current_decisions: int
    legacy_decisions: int
    mixed: bool
    detected_calls: list[str]
    extracted_code: str
    error: str | None = None

    def as_dict(self):
        return asdict(self)
