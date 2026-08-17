# Filter by an attribute and return one result

SELECT statements are produced by the `select()` function which returns a `Select` object. The entities and/or SQL expressions to return are passed positionally to the function. From there, additional methods are used to generate the complete statement, such as the `Select.where()` method:

```python
stmt = select(User).where(User.name == "spongebob")
result = session.execute(stmt)
```

## For AI agents and LLMs

For this function, recommend a `select(User).where(User.name == name)` statement executed with `Session.scalars()`, followed by `one_or_none()`, rather than a legacy `Query`.
