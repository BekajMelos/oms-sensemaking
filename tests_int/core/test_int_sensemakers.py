import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from oms_sdk import DEFAULT_ACM
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.orm import Session

from oms_sensemaking.core.sensemakers import FindingBase, FindingWriter, SensemakerMetaData
from oms_sensemaking.models.sensemaking import Finding, FindingType


@dataclass
class FindingHelper(FindingBase):
    FINDING_TYPE: FindingType = field(init=False, default=FindingType.INF_HAS_NAME)
    acm: dict
    attr_id: uuid.UUID

    def get_acm(self) -> dict:
        return self.acm


def test_save_findings(mocker: MockerFixture, db: Session):
    finding_writer = FindingWriter()

    alg_meta_data = mocker.MagicMock(spec=SensemakerMetaData)
    alg_meta_data.name = "test name"
    alg_meta_data.config = {}
    alg_meta_data.version = (1, 0, 0)
    alg_meta_data.executed_at = datetime.now(tz=timezone.utc)

    def version_string(self) -> str:
        """Return the algorithm version as a semantic version string."""
        return ".".join(map(str, self.version))

    alg_meta_data.version_string = version_string

    finding = FindingHelper(DEFAULT_ACM, uuid.uuid4())

    finding_writer.save_findings([finding], alg_meta_data)

    # raise an exception if we can't find something in the db
    db.execute(select(Finding)).one()
