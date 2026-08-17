Implement this function:

```python
def find_first_user_with_prefix(session, prefix):
    ...
```

Required behavior:

- Return the first User ordered by User.id whose name begins with prefix.
- Return None when no User matches.

The runtime fixture provides mapped `User` and `Address` classes and a SQLAlchemy `Session`. You may import SQLAlchemy APIs. Return only the Python implementation, with no test setup or database configuration.
