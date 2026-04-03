import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Dialect, create_engine
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from oms_sensemaking.models.base import BaseORM, UtcDateTime


class User(BaseORM):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column()


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseORM.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()


def test_get_or_create_creates_new(session):
    user, created = User.get_or_create(session, name="alice", defaults={"email": "alice@example.com"})
    assert created is True
    assert user.id is not None
    assert user.name == "alice"
    assert user.email == "alice@example.com"


def test_get_or_create_returns_existing(session):
    # First insert
    u1, created1 = User.get_or_create(session, name="bob", defaults={"email": "bob@example.com"})
    assert created1 is True

    # Second call should not create new
    u2, created2 = User.get_or_create(session, name="bob", defaults={"email": "new@example.com"})
    assert created2 is False
    assert u1.id == u2.id
    assert u2.email == "bob@example.com"  # unchanged


def test_to_dict_and_to_json(session):
    user, _ = User.get_or_create(session, name="carol", defaults={"email": "carol@example.com"})
    d = user.to_dict()
    assert isinstance(d, dict)
    assert d["name"] == "carol"

    j = user.to_json()
    assert isinstance(j, str)
    loaded = json.loads(j)
    assert loaded["email"] == "carol@example.com"


def test_process_bind_param_converts_to_utc():
    utc_type = UtcDateTime()
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=3)))
    result = utc_type.process_bind_param(dt, Dialect())
    assert result.tzinfo is None
    assert result.hour == 9  # converted from UTC+3 → UTC


def test_process_bind_param_raises_if_naive():
    utc_type = UtcDateTime()
    dt = datetime(2024, 1, 1, 12, 0)  # no tzinfo
    with pytest.raises(TypeError):
        utc_type.process_bind_param(dt, Dialect())


def test_process_result_value_sets_utc():
    utc_type = UtcDateTime()
    stored = datetime(2024, 1, 1, 12, 0)  # naive in DB
    result = utc_type.process_result_value(stored, Dialect())
    assert result.tzinfo == timezone.utc


def test_process_literal_param_returns_iso8601():
    utc_type = UtcDateTime()
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    result = utc_type.process_literal_param(dt, Dialect())
    assert result == dt.isoformat()


def test_process_literal_param_none():
    utc_type = UtcDateTime()
    assert utc_type.process_literal_param(None, Dialect()) is None
