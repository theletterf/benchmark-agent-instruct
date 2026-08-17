# Retrieve an ORM object by primary key

## Required behavior

- Return the matching User.
- Return None when the identifier is absent.

## Current API

For this function, recommend `session.get(User, user_id)` rather than the legacy `Query.get()` form.

`Session.query()` is legacy. Do not mix it with the current API family. Preserve the listed result semantics and stated current operation.
