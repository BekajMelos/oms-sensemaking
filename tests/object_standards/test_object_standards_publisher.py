from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    CompliantObjectInput,
    CreateObjectStandardsInput,
    NodesNodesData,
    ObjectStandardsObjectStandardsData,
    ObjectStandardsViolationInput,
    ObjectType,
    UpdateObjectStandardsInput,
    ViolationType,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.object_standards.object_standards_models import ObjectStandardsGrade
from oms_sensemaking.object_standards.object_standards_publisher import ObjectStandardsATOMSPublisher


@pytest.fixture
def publisher():
    mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)

    return ObjectStandardsATOMSPublisher(
        oms_crud_tool=mock_oms_crud_tool,
    )


def test_publish_results_to_atoms_update(publisher):
    fixed = datetime(2025, 5, 17, 14, 30, tzinfo=timezone.utc)
    existing_obj_standard = MagicMock(spec=ObjectStandardsObjectStandardsData)
    existing_obj_standard.id = uuid4()

    mock_node = MagicMock(spec=NodesNodesData)
    mock_node.id = uuid4()

    rolled_up_acm = DEFAULT_ACM

    violation = ObjectStandardsViolationInput(
        objectType=ObjectType.ATTRIBUTE, iri="attr_iri", violationType=ViolationType.MISSING, description="str"
    )

    compliant_object = CompliantObjectInput(id=uuid4(), objectType=ObjectType.ATTRIBUTE)

    grade = MagicMock(spec=ObjectStandardsGrade)
    grade.float_score = 0.5
    grade.ratio = "1/2"
    grade.violations = [violation]
    grade.compliant_fields = [compliant_object]

    summary = (
        "This object has an Object Standards score of 0.5 (1/2). "
        "This object has 1 violation(s) and 1 compliant object(s)."
    )

    publisher.publish_results_to_atoms(mock_node, [existing_obj_standard], rolled_up_acm, grade, summary, fixed)

    publisher.oms_crud_tool.update_object_standards.assert_called_with(
        UpdateObjectStandardsInput(
            id=existing_obj_standard.id,
            acm=rolled_up_acm,
            summary=summary,
            score=grade.float_score,
            violations=grade.violations,
            compliantObjects=grade.compliant_fields,
            timestamp=fixed,
            standardsVersion=SETTINGS.object_standards_settings.playbook_version,
        )
    )


def test_publish_results_to_atoms_create(publisher):
    fixed = datetime(2025, 5, 17, 14, 30, tzinfo=timezone.utc)
    mock_node = MagicMock(spec=NodesNodesData)
    mock_node.id = uuid4()

    rolled_up_acm = DEFAULT_ACM

    violation = ObjectStandardsViolationInput(
        objectType=ObjectType.ATTRIBUTE, iri="attr_iri", violationType=ViolationType.MISSING, description="str"
    )

    compliant_object = CompliantObjectInput(id=uuid4(), objectType=ObjectType.ATTRIBUTE)

    grade = MagicMock(spec=ObjectStandardsGrade)
    grade.float_score = 0.5
    grade.ratio = "1/2"
    grade.violations = [violation]
    grade.compliant_fields = [compliant_object]

    summary = (
        "This object has an Object Standards score of 0.5 (1/2). "
        "This object has 1 violation(s) and 1 compliant object(s)."
    )

    publisher.publish_results_to_atoms(mock_node, [], rolled_up_acm, grade, summary, fixed)

    publisher.oms_crud_tool.create_object_standards.assert_called_with(
        CreateObjectStandardsInput(
            acm=rolled_up_acm,
            tags=SETTINGS.object_standards_settings.tags,
            nodeId=mock_node.id,
            summary=summary,
            score=grade.float_score,
            violations=grade.violations,
            compliantObjects=grade.compliant_fields,
            timestamp=fixed,
            standardsVersion=SETTINGS.object_standards_settings.playbook_version,
        )
    )
