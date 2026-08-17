# Filter by an attribute and return one result

## SQLAlchemy 2.0 ORM usage

The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method.

## Relevant official documentation

SELECT statements are produced by the `select()` function which returns a `Select` object. The entities and/or SQL expressions to return are passed positionally to the function. From there, additional methods are used to generate the complete statement, such as the `Select.where()` method:

```python
stmt = select(User).where(User.name == "spongebob")
result = session.execute(stmt)
```

## Application behavior

The benchmark fixture asks for a small function and supplies the mapped classes, session, and deterministic data. The implementation must satisfy all of these result semantics:

- Return the User whose name equals name.
- Return None when no User matches.

The distinction between functional behavior and API family matters: legacy `Query` code may still execute successfully even though it does not use the current documented family.

## Recommended approach

For this function, recommend a `select(User).where(User.name == name)` statement executed with `Session.scalars()`, followed by `one_or_none()`, rather than a legacy `Query`.
