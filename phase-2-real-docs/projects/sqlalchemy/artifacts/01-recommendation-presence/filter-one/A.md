# Filter by an attribute and return one result

SELECT statements are produced by the `select()` function which returns a `Select` object. The entities and/or SQL expressions to return are passed positionally to the function. From there, additional methods are used to generate the complete statement, such as the `Select.where()` method:

```python
stmt = select(User).where(User.name == "spongebob")
result = session.execute(stmt)
```
