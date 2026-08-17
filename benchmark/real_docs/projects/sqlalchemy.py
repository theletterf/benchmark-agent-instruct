from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

from ..models import TaskSpec
from ...worlds import ROOT

PROJECT = "sqlalchemy"
VERSION = "2.0.52"
PROJECT_ROOT = ROOT / "phase-2-real-docs" / "projects" / PROJECT
SOURCES = PROJECT_ROOT / "sources"


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)


def source_manifest():
    return json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))


def source_text(source_id):
    item = next(item for item in source_manifest()["sources"] if item["id"] == source_id)
    parser = _TextExtractor()
    parser.feed((SOURCES / item["snapshot"]).read_text(encoding="utf-8"))
    return " ".join(parser.parts)


def validate_sources():
    errors = []
    manifest = source_manifest()
    if manifest.get("documentation_version") != VERSION or manifest.get("runtime_version") != VERSION:
        errors.append("documentation/runtime version is not pinned to 2.0.52")
    for source in manifest["sources"]:
        path = SOURCES / source["snapshot"]
        if not path.exists():
            errors.append(f"missing source snapshot: {source['snapshot']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != source["sha256"]:
            errors.append(f"source hash mismatch: {source['snapshot']}")
        if VERSION not in source_text(source["id"]):
            errors.append(f"source does not identify SQLAlchemy {VERSION}: {source['id']}")
    return errors


COMMON_QUERYING = """The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method."""


TASKS = (
    TaskSpec(
        "primary-key-lookup", "Retrieve an ORM object by primary key", "find_user_by_id", "def find_user_by_id(session, user_id):",
        ("Return the matching User.", "Return None when the identifier is absent."),
        ("migration-20", "legacy-query-api"),
        """The `Query.get()` method remains for legacy purposes, but the primary interface is now the `Session.get()` method:

```python
# legacy usage
user_obj = session.query(User).get(5)

# 1.4 / 2.0 cross-compatible use
user_obj = session.get(User, 5)
```""",
        ("Query.get() method remains for legacy purposes", "primary interface is now the Session.get() method"),
        "For this function, recommend `session.get(User, user_id)` rather than the legacy `Query.get()` form.",
        "def find_user_by_id(session, user_id):\n    return session.get(User, user_id)",
        "def find_user_by_id(session, user_id):\n    return session.query(User).get(user_id)",
        ("Session.get", "select with Session.execute/scalars"), ("Query.get", "Session.query"),
    ),
    TaskSpec(
        "retrieve-all", "Retrieve all mapped objects", "get_all_users", "def get_all_users(session):",
        ("Return all User objects.", "Return them ordered by User.id."),
        ("session-basics", "migration-20"),
        """The primary means of querying is to make use of the `select()` construct to create a `Select` object, which is then executed to return a result using methods such as `Session.execute()` and `Session.scalars()`. Results are then returned in terms of `Result` objects, including sub-variants such as `ScalarResult`.

```python
statement = select(User).filter_by(name="ed")
user_obj = session.scalars(statement).all()
```""",
        ("The primary means of querying is to make use of the select() construct", "Session.execute() and Session.scalars()"),
        "For this function, recommend `session.scalars(select(User).order_by(User.id)).all()` rather than constructing a legacy `Query`.",
        "def get_all_users(session):\n    return session.scalars(select(User).order_by(User.id)).all()",
        "def get_all_users(session):\n    return session.query(User).order_by(User.id).all()",
        ("select", "Session.scalars"), ("Session.query", "Query.all"),
    ),
    TaskSpec(
        "filter-one", "Filter by an attribute and return one result", "find_user_by_name", "def find_user_by_name(session, name):",
        ("Return the User whose name equals name.", "Return None when no User matches."),
        ("orm-querying-guide", "migration-20"),
        """SELECT statements are produced by the `select()` function which returns a `Select` object. The entities and/or SQL expressions to return are passed positionally to the function. From there, additional methods are used to generate the complete statement, such as the `Select.where()` method:

```python
stmt = select(User).where(User.name == "spongebob")
result = session.execute(stmt)
```""",
        ("SELECT statements are produced by the select() function", "additional methods are used to generate the complete statement"),
        "For this function, recommend a `select(User).where(User.name == name)` statement executed with `Session.scalars()`, followed by `one_or_none()`, rather than a legacy `Query`.",
        "def find_user_by_name(session, name):\n    return session.scalars(select(User).where(User.name == name)).one_or_none()",
        "def find_user_by_name(session, name):\n    return session.query(User).filter(User.name == name).one_or_none()",
        ("select", "Session.scalars", "ScalarResult.one_or_none"), ("Session.query", "Query.one_or_none"),
    ),
    TaskSpec(
        "first-matching", "Retrieve the first matching object", "find_first_user_with_prefix", "def find_first_user_with_prefix(session, prefix):",
        ("Return the first User ordered by User.id whose name begins with prefix.", "Return None when no User matches."),
        ("migration-20",),
        """For `first()`, no LIMIT is applied automatically; add `limit(1)` if LIMIT is desired on the query.

```python
user = (
    session.execute(
        select(User).filter_by(name="some user").limit(1)
    ).scalars().first()
)
```""",
        ("for first(), no LIMIT is applied automatically", "add limit(1) if LIMIT"),
        "For this function, recommend `select(User)` with the prefix filter, `order_by(User.id)`, and `limit(1)`, executed through `Session.scalars()` and finished with `first()`, rather than a legacy `Query`.",
        "def find_first_user_with_prefix(session, prefix):\n    stmt = select(User).where(User.name.startswith(prefix)).order_by(User.id).limit(1)\n    return session.scalars(stmt).first()",
        "def find_first_user_with_prefix(session, prefix):\n    return session.query(User).filter(User.name.startswith(prefix)).order_by(User.id).first()",
        ("select", "Session.scalars", "Select.limit", "Result.first"), ("Session.query", "Query.first"),
    ),
    TaskSpec(
        "join-filter", "Join mapped classes and filter by the joined class", "find_user_by_email", "def find_user_by_email(session, email):",
        ("Join User to Address.", "Return the User whose Address.email_address equals email.", "Return None when no address matches."),
        ("orm-querying-guide", "migration-20"),
        """The `Select.join()` and `Select.join_from()` methods are used to construct SQL JOINs against a SELECT statement.

```python
stmt = select(User).join(User.addresses)
for user in session.execute(stmt).scalars():
    ...
```""",
        ("Select.join()", "construct SQL JOINs against a SELECT statement"),
        "For this function, recommend `select(User).join(User.addresses).where(Address.email_address == email)` executed with `Session.scalars()` and finished with `one_or_none()`, rather than a legacy `Query`.",
        "def find_user_by_email(session, email):\n    stmt = select(User).join(User.addresses).where(Address.email_address == email)\n    return session.scalars(stmt).one_or_none()",
        "def find_user_by_email(session, email):\n    return session.query(User).join(User.addresses).filter(Address.email_address == email).one_or_none()",
        ("select", "Select.join", "Session.scalars"), ("Session.query", "Query.join"),
    ),
)


def tasks():
    return list(TASKS)


def task_ids():
    return [task.id for task in TASKS]


def get_task(task_id):
    for task in TASKS:
        if task.id == task_id:
            return task
    raise KeyError(task_id)


def task_prompt(task):
    behavior = "\n".join(f"- {item}" for item in task.behavior)
    return f"""Implement this function:

```python
{task.signature}
    ...
```

Required behavior:

{behavior}

The runtime fixture provides mapped `User` and `Address` classes and a SQLAlchemy `Session`. You may import SQLAlchemy APIs. Return only the Python implementation, with no test setup or database configuration."""


def proposition_manifest(task):
    return {
        "current_api_family": list(task.current_patterns),
        "legacy_api_family": list(task.legacy_patterns),
        "required_behavior": list(task.behavior),
        "recommendation": task.recommendation,
    }
