from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .classifier import classify_code, extract_code
from .models import CodeEvaluation


FIXTURE_PRELUDE = r'''
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    fullname: Mapped[str] = mapped_column(String(80))
    addresses: Mapped[list["Address"]] = relationship(back_populates="user")

class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str] = mapped_column(String(100), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped[User] = relationship(back_populates="addresses")

def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    alice = User(id=1, name="alice", fullname="Alice Adams")
    bob = User(id=2, name="bob", fullname="Bob Brown")
    cara = User(id=3, name="cara", fullname="Cara Cole")
    alice.addresses = [Address(email_address="alice@example.test"), Address(email_address="alice@work.test")]
    bob.addresses = [Address(email_address="bob@example.test")]
    session.add_all([alice, bob, cara])
    session.commit()
    return session
'''


CHECKS = {
    "primary-key-lookup": r'''
with make_session() as session:
    found = find_user_by_id(session, 2)
    check_one = isinstance(found, User) and found.id == 2 and found.name == "bob"
with make_session() as session:
    check_two = find_user_by_id(session, 999) is None
functional = check_one and check_two
''',
    "retrieve-all": r'''
with make_session() as session:
    found = list(get_all_users(session))
    functional = [user.id for user in found] == [1, 2, 3]
''',
    "filter-one": r'''
with make_session() as session:
    found = find_user_by_name(session, "bob")
    check_one = isinstance(found, User) and found.id == 2
with make_session() as session:
    check_two = find_user_by_name(session, "nobody") is None
functional = check_one and check_two
''',
    "first-matching": r'''
with make_session() as session:
    found = find_first_user_with_prefix(session, "a")
    check_one = isinstance(found, User) and found.id == 1
with make_session() as session:
    check_two = find_first_user_with_prefix(session, "z") is None
functional = check_one and check_two
''',
    "join-filter": r'''
with make_session() as session:
    found = find_user_by_email(session, "bob@example.test")
    check_one = isinstance(found, User) and found.id == 2
with make_session() as session:
    check_two = find_user_by_email(session, "missing@example.test") is None
functional = check_one and check_two
''',
}


def evaluate_output(task, output, timeout=8):
    code = extract_code(output, task.function_name)
    classification, current, legacy, calls, mixed = classify_code(task, code)
    try:
        compile(code, "<candidate>", "exec")
    except SyntaxError as exc:
        return CodeEvaluation(False, False, False, classification, current, legacy, mixed, calls, code, f"SyntaxError: {exc.msg}")
    runner = (
        FIXTURE_PRELUDE + "\n" + code + "\n\n"
        "try:\n" + "\n".join("    " + line for line in CHECKS[task.id].splitlines()) + "\n"
        "    print('__BENCHMARK_RESULT__' + json.dumps({'runtime_success': True, 'functional_correct': bool(functional)}))\n"
        "except Exception as exc:\n"
        "    print('__BENCHMARK_RESULT__' + json.dumps({'runtime_success': False, 'functional_correct': False, 'error': type(exc).__name__ + ': ' + str(exc)}))\n"
    )
    # json is deliberately imported after candidate code so the harness retains it.
    runner = "import json\n" + runner
    try:
        with tempfile.TemporaryDirectory(prefix="sqlalchemy-benchmark-") as directory:
            path = Path(directory) / "candidate_runner.py"
            path.write_text(runner, encoding="utf-8")
            process = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return CodeEvaluation(True, False, False, classification, current, legacy, mixed, calls, code, "runtime timeout")
    marker = next((line for line in reversed(process.stdout.splitlines()) if line.startswith("__BENCHMARK_RESULT__")), None)
    if marker is None:
        error = (process.stderr or process.stdout or f"exit code {process.returncode}").strip()[-1000:]
        return CodeEvaluation(True, False, False, classification, current, legacy, mixed, calls, code, error)
    payload = json.loads(marker.removeprefix("__BENCHMARK_RESULT__"))
    return CodeEvaluation(True, bool(payload["runtime_success"]), bool(payload["functional_correct"]), classification, current, legacy, mixed, calls, code, payload.get("error"))
