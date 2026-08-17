"""Small, dependency-free .env loader for local benchmark runs."""

from __future__ import annotations

import os
import re
from pathlib import Path

from .worlds import ROOT

_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_value(raw):
    value = raw.strip()
    if not value:
        return ""
    if value[0] in ("'", '"'):
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise ValueError("unterminated quoted value")
        value = value[1:-1]
        if quote == '"':
            value = value.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t")
            value = value.replace(r'\"', '"').replace(r"\\", "\\")
        return value
    # Treat a whitespace-prefixed # as an inline comment, while preserving #
    # characters that are part of an unquoted value.
    return re.split(r"\s+#", value, maxsplit=1)[0].rstrip()


def load_dotenv(path=None, override=False):
    """Load the nearest project .env without overwriting exported variables."""
    if path is not None:
        candidates = [Path(path)]
    else:
        candidates = [Path.cwd() / ".env"]
        project_env = ROOT / ".env"
        if project_env != candidates[0]:
            candidates.append(project_env)

    env_path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if env_path is None:
        return None, set()

    loaded = set()
    for line_number, original in enumerate(env_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"invalid .env entry at {env_path}:{line_number}")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not _KEY.fullmatch(key):
            raise ValueError(f"invalid .env key at {env_path}:{line_number}")
        value = _parse_value(raw_value)
        if override or key not in os.environ:
            os.environ[key] = value
            loaded.add(key)
    return env_path, loaded
