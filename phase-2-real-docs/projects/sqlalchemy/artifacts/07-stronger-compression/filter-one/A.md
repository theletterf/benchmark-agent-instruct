# Filter by an attribute and return one result

SQLAlchemy 2.x uses the current ORM query family identified below. The older `Session.query()` family remains available as a legacy API, so working legacy code is not the same as current documented code.

## Required behavior

- Return the User whose name equals name.
- Return None when no User matches.

## Current API

For this function, recommend a `select(User).where(User.name == name)` statement executed with `Session.scalars()`, followed by `one_or_none()`, rather than a legacy `Query`.

Use the stated result operation so the function preserves the required missing-result and ordering semantics. Do not combine the current `select()` / `Session` family with a legacy `Query` construction.
