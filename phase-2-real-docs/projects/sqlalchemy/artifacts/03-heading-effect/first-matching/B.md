# Retrieve the first matching object

For `first()`, no LIMIT is applied automatically; add `limit(1)` if LIMIT is desired on the query.

```python
user = (
    session.execute(
        select(User).filter_by(name="some user").limit(1)
    ).scalars().first()
)
```

For this function, recommend `select(User)` with the prefix filter, `order_by(User.id)`, and `limit(1)`, executed through `Session.scalars()` and finished with `first()`, rather than a legacy `Query`.
