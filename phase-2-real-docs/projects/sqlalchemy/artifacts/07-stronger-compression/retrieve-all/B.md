# Retrieve all mapped objects

## Required behavior

- Return all User objects.
- Return them ordered by User.id.

## Current API

For this function, recommend `session.scalars(select(User).order_by(User.id)).all()` rather than constructing a legacy `Query`.

`Session.query()` is legacy. Do not mix it with the current API family. Preserve the listed result semantics and stated current operation.
