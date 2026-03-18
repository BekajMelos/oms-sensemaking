import json
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import AttributeAttribute, NodeNode
from oms_sdk.generated.generated_graphql_client.enums import ObjectTier

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.resolution.sensemaker import DupFinding, DupNodeAndAttributeAcms, ResolutionSensemaker


@pytest.fixture
def test_node():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_node",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )


@pytest.fixture
def test_node_dup(test_node):
    return DupNodeAndAttributeAcms(node=test_node, attribute_acms=[DEFAULT_ACM])


@pytest.fixture
def test_node_a():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_nodeA",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )


@pytest.fixture
def test_node_a_dup(test_node_a):
    return DupNodeAndAttributeAcms(node=test_node_a, attribute_acms=[DEFAULT_ACM])


@pytest.fixture
def test_node_b():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_nodeB",
        tier=ObjectTier.PRIMARY,
        classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
    )


@pytest.fixture
def test_node_b_dup(test_node_b):
    return DupNodeAndAttributeAcms(node=test_node_b, attribute_acms=[DEFAULT_ACM])


@pytest.fixture
def test_node_aircraft_a():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_nodeC",
        tier=ObjectTier.PRIMARY,
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
    )


@pytest.fixture
def test_node_aircraft_a_dup(test_node_aircraft_a):
    return DupNodeAndAttributeAcms(node=test_node_aircraft_a, attribute_acms=[DEFAULT_ACM])


@pytest.fixture
def test_node_aircraft_b():
    return NodeNode.model_construct(
        id=uuid4(),
        acm=DEFAULT_ACM,
        name="test_nodeD",
        tier=ObjectTier.PRIMARY,
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
    )


@pytest.fixture
def test_node_aircraft_b_dup(test_node_aircraft_b):
    return DupNodeAndAttributeAcms(node=test_node_aircraft_b, attribute_acms=[DEFAULT_ACM])


@pytest.fixture
def test_attribute(test_node):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_a(test_node_a):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node_a.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_b(test_node_b):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node_b.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_aircraft_a(test_node_aircraft_a):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasCategoryCode",
        attributeValue="ABC123",
        nodeId=test_node_aircraft_a.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_aircraft_b(test_node_aircraft_b):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasCategoryCode",
        attributeValue="ABC123",
        nodeId=test_node_aircraft_b.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_aircraft_c(test_node_aircraft_a):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasTailNumber",
        attributeValue="T001",
        nodeId=test_node_aircraft_a.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def test_attribute_aircraft_d(test_node_aircraft_b):
    return AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasTailNumber",
        attributeValue="T001",
        nodeId=test_node_aircraft_b.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def duplicate_object_iris():
    with open(SETTINGS.duplicate_object_iris_file_path) as f:
        dup_iris = json.load(f)
        return dup_iris


@pytest.fixture
def mock_crud_tool(test_node):
    mock_tool = mock.MagicMock(spec=OmsCrudTool)
    mock_tool.get_node.return_value = test_node
    return mock_tool


@pytest.fixture
def sensemaker(duplicate_object_iris, mock_crud_tool):
    return ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)


def test_current_class_iri(sensemaker, test_attribute, test_node):
    result = sensemaker.current_class_iri(test_attribute)
    assert result == test_node.classIri


@pytest.mark.parametrize(
    "attr_kwargs",
    [
        {
            "attributeIri": "https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
            "attributeValue": "ABCD1234",
            "nodeId": None,
        },
        {"attributeIri": "fake_attr_iri", "attributeValue": "ABCD1234", "nodeId": uuid4()},
        {
            "attributeIri": "https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
            "attributeValue": "",
            "nodeId": uuid4,
        },
    ],
)
def test_is_valid_false_cases(duplicate_object_iris, attr_kwargs):
    attr = AttributeAttribute.model_construct(**attr_kwargs, sourceId=uuid4(), acm=DEFAULT_ACM)
    mock_crud = mock.MagicMock(spec=OmsCrudTool)
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud)
    result = sensemaker.is_valid(attr)
    assert result == (False, None)


def test_is_valid_false_when_attr_not_in_any_criteria_set(duplicate_object_iris, mock_crud_tool, test_node):
    # Attribute belongs to the Facility node but is NOT part of any criteria set
    bad_attr = AttributeAttribute.model_construct(
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasFacilityName",
        attributeValue="Some Name",
        nodeId=test_node.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )

    # Needed so current_class_iri works
    mock_crud_tool.get_node.return_value = test_node

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    valid, class_iri = sensemaker.is_valid(bad_attr)

    assert valid is False
    assert class_iri is None


def test_is_valid_already_ran_false(duplicate_object_iris, test_attribute, mock_crud_tool):
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    with mock.patch.object(ResolutionSensemaker, "has_already_ran", return_value=True):
        assert sensemaker.is_valid(test_attribute) == (False, None)


def test_is_valid_true_case(duplicate_object_iris, test_attribute, mock_crud_tool):
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    with mock.patch.object(ResolutionSensemaker, "has_already_ran", return_value=False):
        valid, class_iri = sensemaker.is_valid(test_attribute)
        assert valid is True
        assert class_iri == "https://foundry.ai.mil/ontology/4901-001/Facility"


def test_create_duplicate_findings_creates_dups_and_relationships(
    duplicate_object_iris, mock_crud_tool, test_node_dup, test_node_a_dup, test_node_b_dup, test_attribute
):
    # Setup
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    # Call method
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup"):
        dups = sensemaker.create_duplicate_findings(test_attribute, [test_node_dup, test_node_a_dup, test_node_b_dup])

    # Assertions
    assert len(dups) == 2
    assert all(isinstance(d, DupFinding) for d in dups)
    assert dups[0].end_node_id == test_node_a_dup.node.id
    assert dups[1].end_node_id == test_node_b_dup.node.id

    # Check if relationships were created
    assert mock_crud_tool.create_relationship.call_count == 2


def test_has_already_ran_true(duplicate_object_iris, mock_crud_tool):
    mock_crud_tool.get_relationships.return_value.data = [1]  # dummy data

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    assert sensemaker.has_already_ran(uuid4()) is True


def test_has_already_ran_false(duplicate_object_iris, mock_crud_tool):
    mock_crud_tool.get_relationships.return_value.data = []

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    assert sensemaker.has_already_ran(uuid4()) is False


def test_find_duplicates_returns_empty_when_no_group_matches(
    duplicate_object_iris, mock_crud_tool, test_attribute_a, test_attribute_b
):
    # Always return empty for every call
    mock_crud_tool.get_nodes.return_value = mock.MagicMock(data=[])

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    result = sensemaker.find_duplicates([[test_attribute_a], [test_attribute_b]])

    assert result == []
    assert mock_crud_tool.get_nodes.call_count == 2  # tried both groups


def test_find_duplicates_returns_first_nonempty_group(
    duplicate_object_iris,
    mock_crud_tool,
    test_node,
    test_node_a,
    test_node_b,
    test_attribute_a,
    test_attribute_b,
    test_node_a_dup,
    test_node_b_dup,
):
    # Return empty for first group, non-empty for second
    mock_crud_tool.get_nodes.side_effect = [mock.MagicMock(data=[]), mock.MagicMock(data=[test_node_a, test_node_b])]

    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)
    duplicates = sensemaker.find_duplicates([[test_attribute_a], [test_attribute_b]])

    assert duplicates == [test_node_a_dup, test_node_b_dup]


def test_gather_criteria_returns_empty_when_invalid(duplicate_object_iris, mock_crud_tool, test_attribute):
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    # Force is_valid to fail
    with mock.patch.object(ResolutionSensemaker, "is_valid", return_value=(False, None)):
        result = sensemaker.gather_criteria(test_attribute)

    assert result == []


def test_process_data_returns_empty_when_no_criteria(duplicate_object_iris, mock_crud_tool, test_attribute):
    """
    Covers the path where gather_criteria() returns [].
    """
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    # Force gather_criteria to return empty
    with mock.patch.object(ResolutionSensemaker, "gather_criteria", return_value=[]):
        findings = sensemaker.process_data(test_attribute)

    assert findings == []
    mock_crud_tool.create_relationship.assert_not_called()


@pytest.fixture
def facility_dual_criteria_config():
    return {
        "https://foundry.ai.mil/ontology/4901-001/Facility": [
            [
                "https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
                "https://foundry.ai.mil/ontology/4901-001/hasOSuffix",
            ],
            ["https://foundry.ai.mil/ontology/4901-001/hasMIBDBFacilitySurrogateKey"],
        ]
    }


def test_process_data_matches_using_alternate_criteria_set(
    facility_dual_criteria_config, test_node_a, test_node_b, mock_crud_tool
):
    # Trigger on the alternate (SK) attribute
    triggering_attr = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasMIBDBFacilitySurrogateKey",
        attributeValue="SK-999",
        nodeId=test_node_a.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )

    mock_crud_tool.get_node.return_value = test_node_a
    mock_crud_tool.get_nodes.return_value = mock.MagicMock(data=[test_node_b])
    mock_crud_tool.get_node_attribute_by_iri.return_value = []

    sensemaker = ResolutionSensemaker(facility_dual_criteria_config, mock_crud_tool)
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup"):
        findings = sensemaker.process_data(triggering_attr)

    assert len(findings) == 1
    assert findings[0].start_node_id == test_node_a.id
    assert findings[0].end_node_id == test_node_b.id
    assert mock_crud_tool.create_relationship.call_count == 1


def test_process_data_skips_criteria_without_triggering_attr(
    facility_dual_criteria_config, test_node_a, test_node_b, mock_crud_tool
):
    # Trigger on BE_NUMBER (not SK)
    triggering_attr = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="https://foundry.ai.mil/ontology/4901-001/hasBasicEncyclopediaNumber",
        attributeValue="ABCD1234",
        nodeId=test_node_a.id,
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )

    mock_crud_tool.get_node.return_value = test_node_a
    mock_crud_tool.get_nodes.return_value = mock.MagicMock(data=[test_node_b])
    mock_crud_tool.get_node_attribute_by_iri.return_value = []

    sensemaker = ResolutionSensemaker(facility_dual_criteria_config, mock_crud_tool)

    findings = sensemaker.process_data(triggering_attr)

    # We should NOT match using the SK-only set
    assert findings == []


def test_create_duplicate_findings_creates_dups_and_relationships_aircraft(
    duplicate_object_iris, mock_crud_tool, test_node_aircraft_a_dup, test_node_aircraft_b_dup, test_attribute_aircraft_a
):
    # Setup
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    # Call method
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup"):
        dups = sensemaker.create_duplicate_findings(
            test_attribute_aircraft_a, [test_node_aircraft_a_dup, test_node_aircraft_b_dup]
        )

    # Assertions
    assert len(dups) == 1
    assert all(isinstance(d, DupFinding) for d in dups)
    assert dups[0].end_node_id == test_node_aircraft_b_dup.node.id

    # Check if relationships were created
    assert mock_crud_tool.create_relationship.call_count == 1


def test_create_duplicate_findings_creates_dups_and_relationships_aircraft_2_attr(
    duplicate_object_iris, mock_crud_tool, test_node_aircraft_a_dup, test_node_aircraft_b_dup, test_attribute_aircraft_d
):
    # Setup
    sensemaker = ResolutionSensemaker(duplicate_object_iris, mock_crud_tool)

    # Call method
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup"):
        dups = sensemaker.create_duplicate_findings(
            test_attribute_aircraft_d, [test_node_aircraft_a_dup, test_node_aircraft_b_dup]
        )

    # Assertions
    assert len(dups) == 1
    assert all(isinstance(d, DupFinding) for d in dups)
    assert dups[0].end_node_id == test_node_aircraft_a_dup.node.id

    # Check if relationships were created
    assert mock_crud_tool.create_relationship.call_count == 1
