# Retrieve the first matching object

## SQLAlchemy 2.0 ORM usage

The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method.

## Relevant official documentation

For `first()`, no LIMIT is applied automatically; add `limit(1)` if LIMIT is desired on the query.

```python
user = (
    session.execute(
        select(User).filter_by(name="some user").limit(1)
    ).scalars().first()
)
```

## Application behavior

The benchmark fixture asks for a small function and supplies the mapped classes, session, and deterministic data. The implementation must satisfy all of these result semantics:

- Return the first User ordered by User.id whose name begins with prefix.
- Return None when no User matches.

The distinction between functional behavior and API family matters: legacy `Query` code may still execute successfully even though it does not use the current documented family.

## Recommended approach

For this function, recommend `select(User)` with the prefix filter, `order_by(User.id)`, and `limit(1)`, executed through `Session.scalars()` and finished with `first()`, rather than a legacy `Query`.
