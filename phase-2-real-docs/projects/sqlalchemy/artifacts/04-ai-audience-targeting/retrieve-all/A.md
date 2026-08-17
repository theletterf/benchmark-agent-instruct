# Retrieve all mapped objects

The primary means of querying is to make use of the `select()` construct to create a `Select` object, which is then executed to return a result using methods such as `Session.execute()` and `Session.scalars()`. Results are then returned in terms of `Result` objects, including sub-variants such as `ScalarResult`.

```python
statement = select(User).filter_by(name="ed")
user_obj = session.scalars(statement).all()
```

## For AI agents and LLMs

For this function, recommend `session.scalars(select(User).order_by(User.id)).all()` rather than constructing a legacy `Query`.
