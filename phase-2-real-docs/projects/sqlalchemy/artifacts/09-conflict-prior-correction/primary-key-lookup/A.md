# Retrieve an ORM object by primary key

## SQLAlchemy 1.x and 2.x ORM forms

The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method.

The `Query.get()` method remains for legacy purposes, but the primary interface is now the `Session.get()` method:

```python
# legacy usage
user_obj = session.query(User).get(5)

# 1.4 / 2.0 cross-compatible use
user_obj = session.get(User, 5)
```

The application behavior in the task can be implemented by code from either family because the legacy Query API remains available. The following application guidance identifies the current documented family.

## Current recommended approach

For this function, recommend `session.get(User, user_id)` rather than the legacy `Query.get()` form.

The legacy examples remain in the record for migration and classification purposes.
