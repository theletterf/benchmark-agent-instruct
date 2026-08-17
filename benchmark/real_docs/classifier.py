from __future__ import annotations

import ast
import re


def extract_code(output, function_name):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", output, flags=re.IGNORECASE | re.DOTALL)
    candidates = [block.strip() for block in blocks if f"def {function_name}" in block]
    candidates.extend(block.strip() for block in blocks if block.strip() not in candidates)
    candidates.append(output.strip())
    match = re.search(rf"(?m)^\s*def\s+{re.escape(function_name)}\s*\(", output)
    if match:
        candidates.append(output[match.start():].strip())
    for candidate in candidates:
        try:
            tree = ast.parse(candidate)
        except SyntaxError:
            continue
        if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name for node in tree.body):
            return candidate
    return candidates[0] if candidates else ""


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return ""


def classify_code(task, code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "unclassified", 0, 0, [], False
    calls = [_call_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    calls = [name for name in calls if name]
    legacy_calls = [name for name in calls if name.endswith(".query")]
    if task.id == "primary-key-lookup":
        current_calls = [name for name in calls if name.endswith("session.get") or name == "session.get"]
        # Accept another variable name for a Session when it calls get(User, ...).
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
                if isinstance(node.args[0], ast.Name) and node.args[0].id == "User":
                    name = _call_name(node.func)
                    if name not in current_calls:
                        current_calls.append(name)
        # A SELECT-by-primary-key is also part of the documented SQLAlchemy
        # 2.x family even though Session.get() is the primary recommendation.
        has_select = any(name == "select" or name.endswith(".select") for name in calls)
        if has_select:
            current_calls.extend(name for name in calls if name.endswith(".scalars") or name.endswith(".execute"))
    else:
        has_select = any(name == "select" or name.endswith(".select") for name in calls)
        execution = [name for name in calls if name.endswith(".scalars") or name.endswith(".execute")]
        current_calls = execution if has_select else []
    current_count, legacy_count = len(current_calls), len(legacy_calls)
    mixed = current_count > 0 and legacy_count > 0
    classification = "mixed" if mixed else "current" if current_count else "legacy" if legacy_count else "unclassified"
    return classification, current_count, legacy_count, calls, mixed
