import re

from .models import Score
from .worlds import alternative_path, preferred_path, step_key


def positions(text, steps):
    lowered = text.lower()
    found = []
    for step in steps:
        token = step_key(step)
        match = re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", lowered)
        found.append(-1 if match is None else match.start())
    return found


def ordered(found):
    return bool(found) and all(position >= 0 for position in found) and found == sorted(found)


def _numbered_step_count(output):
    return len(re.findall(r"(?m)^\s*\d+[.)]\s+\S", output))


def score(world, output):
    preferred = preferred_path(world)
    alternative = alternative_path(world)
    p_positions = positions(output, preferred["steps"])
    a_positions = positions(output, alternative["steps"])
    p_complete = ordered(p_positions)
    a_complete = ordered(a_positions)
    p_any = any(position >= 0 for position in p_positions)
    a_any = any(position >= 0 for position in a_positions)
    numbered_count = _numbered_step_count(output)
    format_ok = numbered_count == 3
    both = p_complete and a_complete
    mixed = p_any and a_any
    preferred_ok = p_complete and not a_any and format_ok
    alternative_ok = a_complete and not p_any and format_ok
    world_correct = preferred_ok or alternative_ok
    invalid = both or mixed or not world_correct
    matched = [step["id"] for step, pos in zip(preferred["steps"], p_positions) if pos >= 0]
    alt_matched = [step["id"] for step, pos in zip(alternative["steps"], a_positions) if pos >= 0]
    return Score(
        world_correct, preferred_ok, alternative_ok, mixed, invalid,
        (p_complete or a_complete) and format_ok, matched, alt_matched,
    )
