# Retrieve all mapped objects

## SQLAlchemy 1.x and 2.x ORM forms

The biggest visible change in SQLAlchemy 2.0 is the use of `Session.execute()` in conjunction with `select()` to run ORM queries, instead of using `Session.query()`. As mentioned elsewhere, there is no plan to actually remove the `Session.query()` API itself, as it is now implemented by using the new API internally it will remain as a legacy API, and both APIs can be used freely.

The `Query` object (as well as the `BakedQuery` and `ShardedQuery` extensions) become long term legacy objects, replaced by the direct usage of the `select()` construct in conjunction with the `Session.execute()` method.

The primary means of querying is to make use of the `select()` construct to create a `Select` object, which is then executed to return a result using methods such as `Session.execute()` and `Session.scalars()`. Results are then returned in terms of `Result` objects, including sub-variants such as `ScalarResult`.

```python
statement = select(User).filter_by(name="ed")
user_obj = session.scalars(statement).all()
```

The application behavior in the task can be implemented by code from either family because the legacy Query API remains available. The following application guidance identifies the current documented family. For this function, recommend `session.scalars(select(User).order_by(User.id)).all()` rather than constructing a legacy `Query`. The legacy examples remain in the record for migration and classification purposes.
