from unittest.mock import MagicMock

import pytest
from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.resolution.attribute_combinations import AttributeCombinations, Criteria


def test_criteria_without_excludes_target():
    c = Criteria(["iri1", "iri2", "iri3"])
    result = c.without("iri2")
    assert result == ["iri1", "iri3"]

def test_criteria_len():
    c = Criteria(["iri1", "iri2", "iri3"])
    assert len(c) == 3

@pytest.fixture
def mock_attribute():
    attr = MagicMock(spec=AttributeAttribute)
    attr.attributeIri = "iri1"
    attr.nodeId = "node123"
    attr.attributeValue = "value1"
    return attr

@pytest.fixture
def mock_oms_crud_tool():
    return MagicMock()

@pytest.fixture
def duplicate_object_iris():
    return {"node123": ["iri1", "iri2"]}

def test_gather_with_single_criteria(mock_attribute, mock_oms_crud_tool):
    # only one IRI, so just returns current attribute in list
    combiner = AttributeCombinations(mock_attribute, mock_oms_crud_tool, {"node123": ["iri1"]})
    result = combiner.gather("node123")
    assert result == [[mock_attribute]]

def test_gather_with_multiple_criteria(mock_attribute, mock_oms_crud_tool, duplicate_object_iris):
    other_attr = MagicMock(spec=AttributeAttribute)
    other_attr.attributeIri = "iri2"
    other_attr.attributeValue = "value2"

    mock_oms_crud_tool.get_node_attribute_by_iri.return_value = [other_attr]

    combiner = AttributeCombinations(mock_attribute, mock_oms_crud_tool, duplicate_object_iris)
    result = combiner.gather("node123")

    assert isinstance(result, list)
    assert any(len(group) == 2 for group in result)  # should include current + one other
    for group in result:
        assert all(attr.attributeValue != "" for attr in group)

def test_attribute_combinator_filters_empty_values(mock_attribute):
    attr1 = MagicMock(spec=AttributeAttribute)
    attr1.attributeIri = "iri2"
    attr1.attributeValue = "value2"

    attr2 = MagicMock(spec=AttributeAttribute)
    attr2.attributeIri = "iri2"
    attr2.attributeValue = ""  # Should be excluded

    combiner = AttributeCombinations(mock_attribute, MagicMock(), {})
    result = combiner.attribute_combinator([attr1, attr2])

    # Should only contain combinations with attr1, not attr2
    assert len(result) == 1
    assert result[0] == [mock_attribute, attr1]

def test_attribute_combinator_with_multiple_attrs(mock_attribute):
    attr1 = MagicMock(spec=AttributeAttribute)
    attr1.attributeIri = "iri2"
    attr1.attributeValue = "value2"

    attr2 = MagicMock(spec=AttributeAttribute)
    attr2.attributeIri = "iri3"
    attr2.attributeValue = "value3"

    combiner = AttributeCombinations(mock_attribute, MagicMock(), {})
    result = combiner.attribute_combinator([attr1, attr2])

    assert len(result) == 1
    assert result[0][0] == mock_attribute
    assert set(result[0][1:]) == {attr1, attr2}
