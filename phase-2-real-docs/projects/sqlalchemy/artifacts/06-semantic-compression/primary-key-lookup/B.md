# Retrieve an ORM object by primary key

SQLAlchemy 2.x uses the current ORM query family identified below. The older `Session.query()` family remains available as a legacy API, so working legacy code is not the same as current documented code.

## Required behavior

- Return the matching User.
- Return None when the identifier is absent.

## Current API

For this function, recommend `session.get(User, user_id)` rather than the legacy `Query.get()` form.

Use the stated result operation so the function preserves the required missing-result and ordering semantics. Do not combine the current `select()` / `Session` family with a legacy `Query` construction.
