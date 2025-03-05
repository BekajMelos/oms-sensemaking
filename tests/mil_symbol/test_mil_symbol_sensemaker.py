"""MilSymbol Sensemaker Unit Tests"""
from typing import Dict, List
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
    NodeNode,
    OntologyClassOntologyClass,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker, SymbolCodeUpdate


@pytest.fixture
def mock_oms_crud_tool():

    oms_crud_tool = OmsCrudTool()
    oms_crud_tool.oms_client = mock.MagicMock()
    return oms_crud_tool

@pytest.fixture
def oms_node() -> NodeNode:
    node = NodeNode.model_construct(
        id=uuid4(),
        classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        name="test",
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
        symbolIdCode=None
    )

    return node


def create_attribute(attribute_iri = None, attribute_value = None) -> AttributeAttribute:
    attr = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri=attribute_iri,
        attributeValue=attribute_value,
        sourceId=uuid4(),
        acm=DEFAULT_ACM
    )

    return attr


def test_process_data(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    # case 1
    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="hostile"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="damaged"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"])
    oms_node.symbolIdCode = "10-0-0-30-0-0-32-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 2
    code_d, code_c = symbols
    assert code_d.new_symbol_id_code == "10-0-6-30-3-0-32-000000-00-00"
    assert code_c.new_symbol_id_code == "SHSD------*****"

    # case 2
    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction", attribute_value="true"))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="suspect"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="destroyed"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"])
    oms_node.symbolIdCode = "10-0-0-01-0-0-00-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 2
    code_d, code_c = symbols
    assert code_d.new_symbol_id_code == "10-2-5-01-4-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SSAX------*****"

    # case 3
    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="friendly"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="present"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"])
    oms_node.symbolIdCode = "10-0-0-01-0-0-00-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 2
    code_d, code_c = symbols
    assert code_d.new_symbol_id_code == "10-0-3-05-0-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SFPP------*****"


def test_get_starting_symbol_id_code(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    # Don't actually get the ontology class from API
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()

    # Test that the node's symbol code is used if set
    oms_node.symbolIdCode = "10-1-1-01-1-1-11-000000-00-00"
    code = sensemaker.get_starting_symbol_id_code(oms_node)

    # make sure we just used the node's symbolIdCode
    mock_oms_crud_tool.get_ontology_class.assert_not_called()
    assert code == "10-1-1-01-1-1-11-000000-00-00"

    # Test that we search the ontology for a default code
    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/SmallTouringHelicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode="10-0-0-01-0-0-00-000000-00-00",
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/Helicopter")
            ])
    ]

    # if code is not present, try to get a default code
    oms_node.symbolIdCode = None
    code = sensemaker.get_starting_symbol_id_code(oms_node)
    assert code == "10-0-0-01-0-0-00-000000-00-00"


def test_get_default_symbol_id_code_regular_traversal(
        mock_oms_crud_tool: OmsCrudTool,
        mil_symbol_rules: Dict):
    """Test traversing ontology for parent classes with codes"""

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/Helicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/Helicopter",
            defaultSymbolIdCode="10-0-0-01-0-0-00-000000-00-00")
    ]

    initial_iri = "http://omsb/test/SmallTouringHelicopter"
    code = sensemaker.get_default_symbol_id_code(initial_iri)
    assert code == "10-0-0-01-0-0-00-000000-00-00"


def test_get_default_symbol_id_code_no_parents(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):
    """test get_default_symbol_id_code when there's no code and no parents to traverse"""

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            parentOntologyClasses=[],
            defaultSymbolIdCode=None)
    ]

    initial_iri = "http://omsb/test/SmallTouringHelicopter"
    code = sensemaker.get_default_symbol_id_code(initial_iri)
    assert code is None


def test_get_context(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):
    """Test that we get the context correctly"""

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    sensemaker.get_context(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(query=AttributeQuery(
            attributeIris=
                SETTINGS.mil_symbol_settings.is_reality_context_iris +
                SETTINGS.mil_symbol_settings.is_exercise_context_iris +
                SETTINGS.mil_symbol_settings.is_simulation_context_iris
            ,
            nodeIds=[oms_node.id]
        ))


def test_get_affiliation(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):
    """Test that we get the affiliation correctly"""

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    sensemaker.get_affiliation(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(query=AttributeQuery(
            attributeIris=SETTINGS.mil_symbol_settings.affiliation_iris,
            nodeIds=[oms_node.id]
        ))


def test_get_status(mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, mil_symbol_rules: Dict):

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    sensemaker.get_status(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(query=AttributeQuery(
            attributeIris=SETTINGS.mil_symbol_settings.status_iris,
            nodeIds=[oms_node.id]
        ))


def test_get_node_ancestors_iris(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):
    """Test get ancestor's iris."""

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    oms_node.classIri = "http://omsb/test/SmallTouringHelicopter"

    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/Helicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/Helicopter",
            defaultSymbolIdCode="10-0-0-01-0-0-00-000000-00-00",
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[]),
    ]

    iris = sensemaker.get_node_ancestors_iris(oms_node)
    assert iris == [
        "http://omsb/test/TouringHelicopter",
        "http://omsb/test/Helicopter",
        "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
    ]


def test_dimension_enrichment(
        mock_oms_crud_tool: OmsCrudTool,
        oms_node: NodeNode,
        mil_symbol_rules: Dict):
    """Test that the dimension is updated based on the parent IRIs"""

    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool)

    # mock getting the ontology classes
    # UnknownHelicopter is not in dimension rules but Aircraft is so should use Air dimension values
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/UnknownHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://purl.obolibrary.org/obo/BFO_0000040")
            ]),
        OntologyClassOntologyClass.model_construct(
            iri="http://purl.obolibrary.org/obo/BFO_0000040",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[]
            )
    ]

    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="hostile"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="damaged"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=[
            "http://omsb/test/TouringHelicopter",
            "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            "http://purl.obolibrary.org/obo/BFO_0000040"])
    oms_node.symbolIdCode = None
    oms_node.classIri = "http://omsb/test/UnknownHelicopter"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 2
    code_d, code_c = symbols

    # The parent IRI makes sure we get the correct dimension of 01
    assert code_d.new_symbol_id_code == "10-0-6-01-3-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SHAD------*****"
