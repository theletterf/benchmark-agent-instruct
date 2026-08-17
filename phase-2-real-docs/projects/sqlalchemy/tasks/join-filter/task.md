Implement this function:

```python
def find_user_by_email(session, email):
    ...
```

Required behavior:

- Join User to Address.
- Return the User whose Address.email_address equals email.
- Return None when no address matches.

The runtime fixture provides mapped `User` and `Address` classes and a SQLAlchemy `Session`. You may import SQLAlchemy APIs. Return only the Python implementation, with no test setup or database configuration.
