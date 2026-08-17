# Retrieve all mapped objects

SQLAlchemy 2.x uses the current ORM query family identified below. The older `Session.query()` family remains available as a legacy API, so working legacy code is not the same as current documented code.

## Required behavior

- Return all User objects.
- Return them ordered by User.id.

## Current API

For this function, recommend `session.scalars(select(User).order_by(User.id)).all()` rather than constructing a legacy `Query`.

Use the stated result operation so the function preserves the required missing-result and ordering semantics. Do not combine the current `select()` / `Session` family with a legacy `Query` construction.
