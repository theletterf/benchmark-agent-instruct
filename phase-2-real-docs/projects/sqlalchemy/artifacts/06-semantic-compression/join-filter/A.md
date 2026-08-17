# Join mapped classes and filter by the joined class

## SQLAlchemy 2.0 ORM usage

The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method.

## Relevant official documentation

The `Select.join()` and `Select.join_from()` methods are used to construct SQL JOINs against a SELECT statement.

```python
stmt = select(User).join(User.addresses)
for user in session.execute(stmt).scalars():
    ...
```

## Application behavior

The benchmark fixture asks for a small function and supplies the mapped classes, session, and deterministic data. The implementation must satisfy all of these result semantics:

- Join User to Address.
- Return the User whose Address.email_address equals email.
- Return None when no address matches.

The distinction between functional behavior and API family matters: legacy `Query` code may still execute successfully even though it does not use the current documented family.

## Recommended approach

For this function, recommend `select(User).join(User.addresses).where(Address.email_address == email)` executed with `Session.scalars()` and finished with `one_or_none()`, rather than a legacy `Query`.
