# Filter by an attribute and return one result

## Required behavior

- Return the User whose name equals name.
- Return None when no User matches.

## Current API

For this function, recommend a `select(User).where(User.name == name)` statement executed with `Session.scalars()`, followed by `one_or_none()`, rather than a legacy `Query`.

`Session.query()` is legacy. Do not mix it with the current API family. Preserve the listed result semantics and stated current operation.
