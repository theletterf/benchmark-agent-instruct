# SQLite fixture

The executable fixture is implemented in `benchmark.real_docs.fixture` and pinned to SQLAlchemy 2.0.52. It creates an in-memory SQLite database with mapped `User` and `Address` classes and deterministic seed data. Generated answers provide only one requested function; the harness supplies all setup.
