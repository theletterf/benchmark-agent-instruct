# Join mapped classes and filter by the joined class

SQLAlchemy 2.x uses the current ORM query family identified below. The older `Session.query()` family remains available as a legacy API, so working legacy code is not the same as current documented code.

## Required behavior

- Join User to Address.
- Return the User whose Address.email_address equals email.
- Return None when no address matches.

## Current API

For this function, recommend `select(User).join(User.addresses).where(Address.email_address == email)` executed with `Session.scalars()` and finished with `one_or_none()`, rather than a legacy `Query`.

Use the stated result operation so the function preserves the required missing-result and ordering semantics. Do not combine the current `select()` / `Session` family with a legacy `Query` construction.
