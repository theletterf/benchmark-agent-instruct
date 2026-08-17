# Retrieve an ORM object by primary key

The `Query.get()` method remains for legacy purposes, but the primary interface is now the `Session.get()` method:

```python
# legacy usage
user_obj = session.query(User).get(5)

# 1.4 / 2.0 cross-compatible use
user_obj = session.get(User, 5)
```

## Recommended approach

For this function, recommend `session.get(User, user_id)` rather than the legacy `Query.get()` form.
