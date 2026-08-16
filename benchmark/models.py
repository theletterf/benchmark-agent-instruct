from dataclasses import asdict, dataclass


@dataclass
class Score:
    world_correct: bool
    preferred_path: bool
    alternative_path: bool
    mixed_path: bool
    invalid_answer: bool
    sequence_correct: bool
    matched_steps: list[str]
    alternative_steps: list[str]

    def as_dict(self):
        return asdict(self)
