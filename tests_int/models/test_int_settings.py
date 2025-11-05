"""Tests for settings ORM models."""

from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from oms_sensemaking.models.settings import Setting


@pytest.fixture
def tester_db(db: Session) -> Iterator[Session]:
    setting_1: Setting = Setting("test_int", 1)
    setting_2: Setting = Setting("test_bool", True)
    setting_3: Setting = Setting("test_string", "Some string setting")
    setting_4: Setting = Setting("test_object", {"primary": 1, "secondary": False})

    db.add(setting_1)
    db.add(setting_2)
    db.add(setting_3)
    db.add(setting_4)
    db.commit()

    yield db


def test_get_or_create_setting_record(tester_db: Session):
    # get a specific setting
    stmt_int = select(Setting).where(Setting.field_name == "test_int")
    setting_int: Setting = tester_db.execute(stmt_int).scalars().one()

    stmt_bool = select(Setting).where(Setting.field_name == "test_bool")
    setting_bool: Setting = tester_db.execute(stmt_bool).scalars().one()

    stmt_string = select(Setting).where(Setting.field_name == "test_string")
    setting_string: Setting = tester_db.execute(stmt_string).scalars().one()

    stmt_object = select(Setting).where(Setting.field_name == "test_object")
    setting_object: Setting = tester_db.execute(stmt_object).scalars().one()

    assert setting_int
    assert setting_int.field_value == 1

    assert setting_bool
    assert setting_bool.field_value

    assert setting_string
    assert setting_string.field_value == "Some string setting"

    assert setting_object
    assert setting_object.field_value == {"primary": 1, "secondary": False}


def test_get_or_create_new_setting(db: Session):
    setting, is_new = Setting.get_or_create(
        db, defaults=dict(field_name="new_setting", field_value="this is a new setting")
    )

    assert setting
    assert is_new

    # Test second call to get the same setting
    same_setting, is_new_again = Setting.get_or_create(
        db, defaults=dict(field_name="new_setting", field_value="this is a new setting")
    )

    assert same_setting.setting_id == setting.setting_id
    assert not is_new_again
