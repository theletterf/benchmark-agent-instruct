# Retrieve the first matching object

For `first()`, no LIMIT is applied automatically; add `limit(1)` if LIMIT is desired on the query.

```python
user = (
    session.execute(
        select(User).filter_by(name="some user").limit(1)
    ).scalars().first()
)
```
