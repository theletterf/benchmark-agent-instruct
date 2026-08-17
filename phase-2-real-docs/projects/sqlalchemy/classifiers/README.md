# SQLAlchemy API classifiers

The classifier is implemented in `benchmark.real_docs.classifier`. It inspects Python AST call structure to distinguish the SQLAlchemy 2.x `Session.get()` / `select()` execution family from the legacy `Session.query()` family. Runtime and functional scores are calculated separately.
