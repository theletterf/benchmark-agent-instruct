# Join mapped classes and filter by the joined class

The `Select.join()` and `Select.join_from()` methods are used to construct SQL JOINs against a SELECT statement.

```python
stmt = select(User).join(User.addresses)
for user in session.execute(stmt).scalars():
    ...
```

For this function, recommend `select(User).join(User.addresses).where(Address.email_address == email)` executed with `Session.scalars()` and finished with `one_or_none()`, rather than a legacy `Query`.
