# Retrieve the first matching object

## Required behavior

- Return the first User ordered by User.id whose name begins with prefix.
- Return None when no User matches.

## Current API

For this function, recommend `select(User)` with the prefix filter, `order_by(User.id)`, and `limit(1)`, executed through `Session.scalars()` and finished with `first()`, rather than a legacy `Query`.

`Session.query()` is legacy. Do not mix it with the current API family. Preserve the listed result semantics and stated current operation.
