"""Tests for geo ORM models."""

from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from sqlalchemy import select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from oms_sensemaking.models.sensemaking import Finding, FindingType

FINDING_ID_1: UUID = UUID("f604f7d3-b78d-49af-a2cf-75eae08cec52")
FINDING_ID_2: UUID = UUID("6796b293-e0b2-4ba3-a361-c59c6e07248b")


@pytest.fixture
def tester_db(db: Session) -> Iterator[Session]:
    finding_1: Finding = Finding(
        DEFAULT_ACM,
        "FooSensemaker",
        "1.0.0",
        {},
        datetime.now(timezone.utc),
        FindingType.UNKNOWN,
        {"msg": "yo!"},
        "Grimlock-INC-36",
        None,
        FINDING_ID_1,
    )

    finding_2: Finding = Finding(
        DEFAULT_ACM,
        "BarSensemaker",
        "1.0.0",
        {},
        datetime.now(timezone.utc),
        FindingType.UNKNOWN,
        {"msg": "yo!"},
        "Grimlock-INC-36",
        None,
        FINDING_ID_2,
    )

    db.add(finding_1)
    db.add(finding_2)
    db.add(
        Finding(
            DEFAULT_ACM,
            "BarSensemaker",
            "1.0.0",
            {},
            datetime.now(timezone.utc),
            FindingType.UNKNOWN,
            {"msg": "yo!"},
            "Grimlock-INC-36",
            None,
            uuid4(),
        )
    )

    db.commit()

    yield db


def test_get_or_create_existing_record(tester_db: Session):
    # get a specific finding
    finding: Finding = tester_db.execute(select(Finding).where(Finding.finding_id == FINDING_ID_1)).scalars().one()

    assert finding


def test_get_or_create_new_record(db: Session):
    finding, is_new = Finding.get_or_create(
        db,
        defaults=dict(
            acm=DEFAULT_ACM,
            finding_id=FINDING_ID_1,
            finding_type=FindingType.UNKNOWN,
            finding_data={"msg": "Test message"},
            oms_version="?",
            published_at=None,
            algorithm_name="",
            algorithm_version="1.0.0",
            algorithm_configuration={},
            executed_at=datetime.now(timezone.utc),
        ),
        finding_id=FINDING_ID_1,
    )

    assert finding
    assert is_new


def test_point_updated_at_no_timezone(tester_db: Session):
    finding_id: UUID = uuid4()

    finding, is_new = Finding.get_or_create(
        tester_db,
        defaults=dict(
            acm=DEFAULT_ACM,
            finding_id=finding_id,
            finding_type=FindingType.UNKNOWN,
            finding_data={"msg": "Test message"},
            oms_version="?",
            published_at=None,
            algorithm_name="",
            algorithm_version="1.0.0",
            algorithm_configuration={},
            executed_at=datetime.now(timezone.utc),
        ),
        finding_id=finding_id,
    )

    assert finding
    assert is_new

    tester_db.add(finding)
    tester_db.commit()
    tester_db.refresh(finding)

    finding.updated_at = datetime.now()
    tester_db.add(finding)

    with pytest.raises(StatementError):
        tester_db.commit()
