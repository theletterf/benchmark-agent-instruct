# Join mapped classes and filter by the joined class

## Required behavior

- Join User to Address.
- Return the User whose Address.email_address equals email.
- Return None when no address matches.

## Current API

For this function, recommend `select(User).join(User.addresses).where(Address.email_address == email)` executed with `Session.scalars()` and finished with `one_or_none()`, rather than a legacy `Query`.

`Session.query()` is legacy. Do not mix it with the current API family. Preserve the listed result semantics and stated current operation.
