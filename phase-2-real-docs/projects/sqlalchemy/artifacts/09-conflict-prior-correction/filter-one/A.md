# Filter by an attribute and return one result

## SQLAlchemy 1.x and 2.x ORM forms

The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method.

SELECT statements are produced by the `select()` function which returns a `Select` object. The entities and/or SQL expressions to return are passed positionally to the function. From there, additional methods are used to generate the complete statement, such as the `Select.where()` method:

```python
stmt = select(User).where(User.name == "spongebob")
result = session.execute(stmt)
```

The application behavior in the task can be implemented by code from either family because the legacy Query API remains available. The following application guidance identifies the current documented family.

## Current recommended approach

For this function, recommend a `select(User).where(User.name == name)` statement executed with `Session.scalars()`, followed by `one_or_none()`, rather than a legacy `Query`.

The legacy examples remain in the record for migration and classification purposes.
