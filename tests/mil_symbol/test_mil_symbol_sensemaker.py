"""MilSymbol Sensemaker Unit Tests"""

from typing import Dict, List
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
    AttributesAttributes,
    NodeNode,
    NodesNodes,
    ObjectTier,
    OntologyClassOntologyClass,
)

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.ontology_client import OntologyClient
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
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        name="test",
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
        symbolIdCode=None,
        tier=ObjectTier.PRIMARY,
        labels=[],
    )

    return node


@pytest.fixture
def oms_object() -> AttributeAttribute:
    attribute_val = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeIri="http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value",
        attributeValue="attributeValue",
        sourceId=uuid4(),
        acm=DEFAULT_ACM,
    )
    return attribute_val


@pytest.fixture
def build_sensemaker(mock_oms_crud_tool: OmsCrudTool, mil_symbol_rules: Dict):
    sensemaker = MilSymbolSensemaker(mil_symbol_rules, mock_oms_crud_tool, OntologyClient(mock_oms_crud_tool))
    return sensemaker


def create_attribute(attribute_iri=None, attribute_value=None, acm=DEFAULT_ACM) -> AttributeAttribute:
    attr = AttributeAttribute.model_construct(
        id=uuid4(), attributeIri=attribute_iri, attributeValue=attribute_value, sourceId=uuid4(), acm=acm
    )

    return attr


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_process_data(
    mock_get_acm: AacClient, mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker
):
    sensemaker = build_sensemaker
    ### Mocks
    ## Mock getting acm
    mock_get_acm.return_value = DEFAULT_ACM

    # case 1
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="hostile"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="damaged"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))
    oms_node.symbolIdCode = "10-0-0-30-0-0-32-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols
    assert code_d.new_symbol_id_code == "10-0-6-30-3-0-32-000000-00-00"
    assert code_c.new_symbol_id_code == "SHSD------*****"
    assert code_b.new_symbol_id_code == "SHSD------*****"

    # case 2
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction", attribute_value="true"
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="suspect"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="destroyed"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    oms_node.symbolIdCode = "10-0-0-01-0-0-00-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols
    assert code_d.new_symbol_id_code == "10-2-5-01-4-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SSAX------*****"
    assert code_b.new_symbol_id_code == "SSAX------*****"

    # case 3
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="friendly"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="present"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    oms_node.symbolIdCode = "spzp------*****"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols
    assert code_d.new_symbol_id_code == "10-0-3-05-0-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SFPP------*****"
    assert code_b.new_symbol_id_code == "SFPP------*****"


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_correct_updates_made_when_none_specified(
    mock_get_acm: AacClient, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker
):
    sensemaker = build_sensemaker
    mock_get_acm.return_value = DEFAULT_ACM
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="none specified"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="present"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    oms_node.symbolIdCode = "sopp------*****"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols
    assert code_d.new_symbol_id_code == "10-0-1-05-0-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SUPP------*****"
    assert code_b.new_symbol_id_code == "SOPP------*****"


def test_get_starting_symbol_id_code_from_attribute_with_valid_mil_symbol(
    oms_node: NodeNode, oms_object: AttributeAttribute, build_sensemaker: MilSymbolSensemaker
):
    sensemaker = build_sensemaker

    # Case where oms_object is an attribute and returns a valid mil symbol attributeIris
    code = sensemaker.get_starting_symbol_id_code(oms_object, oms_node)
    assert code == "attributeValue"


def test_get_starting_symbol_id_code_from_attribute_with_no_valid_mil_symbol(
    oms_node: NodeNode, oms_object: AttributeAttribute, build_sensemaker: MilSymbolSensemaker
):
    sensemaker = build_sensemaker

    # Case where oms_object is an attribute that does not have a valid milsymbol attributeIri and node has symboldIdCode
    oms_object.attributeIri = "invalidIri"
    oms_node.symbolIdCode = "symbol_id_code"
    code = sensemaker.get_starting_symbol_id_code(oms_object, oms_node)
    assert code == "symbol_id_code"


def test_get_starting_symbol_id_code_from_node_with_symbol_id_code(
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    oms_object: AttributeAttribute,
    build_sensemaker: MilSymbolSensemaker,
):
    sensemaker = build_sensemaker

    # Don't actually get the ontology class from API
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()

    # Case where oms_object is not an attribute but is an oms_node with a symbol_id_code
    oms_node.symbolIdCode = "symbol_id_code"
    oms_object = oms_node
    code = sensemaker.get_starting_symbol_id_code(oms_object, oms_node)

    # make sure we just used the node's symbolIdCode
    mock_oms_crud_tool.get_ontology_class.assert_not_called()

    assert code == "symbol_id_code"


def test_get_starting_symbol_id_code(
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    oms_object: AttributeAttribute,
    build_sensemaker: MilSymbolSensemaker,
):
    sensemaker = build_sensemaker

    # Don't actually get the ontology class from API
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()

    # Test that we search the ontology for a default code
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/SmallTouringHelicopter")
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode="10-0-0-01-0-0-00-000000-00-00",
            parentOntologyClasses=[OntologyClassOntologyClass.model_construct(iri="http://omsb/test/Helicopter")],
        ),
    ]

    # if code is not present, try to get a default code
    oms_node.symbolIdCode = None
    oms_object.attributeIri = "fakeIri"
    code = sensemaker.get_starting_symbol_id_code(oms_object, oms_node)
    assert code == "10-0-0-01-0-0-00-000000-00-00"


def test_get_default_symbol_id_code_regular_traversal(
    mock_oms_crud_tool: OmsCrudTool, build_sensemaker: MilSymbolSensemaker
):
    """Test traversing ontology for parent classes with codes"""

    sensemaker = build_sensemaker

    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[OntologyClassOntologyClass.model_construct(iri="http://omsb/test/Helicopter")],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/Helicopter", defaultSymbolIdCode="10-0-0-01-0-0-00-000000-00-00"
        ),
    ]

    initial_iri = "http://omsb/test/SmallTouringHelicopter"
    code = sensemaker.get_default_symbol_id_code(initial_iri)
    assert code == "10-0-0-01-0-0-00-000000-00-00"


def test_get_default_symbol_id_code_no_parents(mock_oms_crud_tool: OmsCrudTool, build_sensemaker: MilSymbolSensemaker):
    """test get_default_symbol_id_code when there's no code and no parents to traverse"""

    sensemaker = build_sensemaker

    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter", parentOntologyClasses=[], defaultSymbolIdCode=None
        )
    ]

    initial_iri = "http://omsb/test/SmallTouringHelicopter"
    code = sensemaker.get_default_symbol_id_code(initial_iri)
    assert code is None


def test_get_context(mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker):
    """Test that we get the context correctly"""

    sensemaker = build_sensemaker

    sensemaker.get_context(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(
        query=AttributeQuery(
            attributeIris=SETTINGS.mil_symbol_settings.is_reality_context_iris
            + SETTINGS.mil_symbol_settings.is_exercise_context_iris
            + SETTINGS.mil_symbol_settings.is_simulation_context_iris,
            nodeIds=[oms_node.id],
        )
    )


def test_get_affiliation(mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker):
    """Test that we get the affiliation correctly"""

    sensemaker = build_sensemaker

    sensemaker.get_affiliation(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(
        query=AttributeQuery(attributeIris=SETTINGS.mil_symbol_settings.affiliation_iris, nodeIds=[oms_node.id])
    )


def test_get_status(mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker):
    sensemaker = build_sensemaker

    sensemaker.get_status(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(
        query=AttributeQuery(attributeIris=SETTINGS.mil_symbol_settings.status_iris, nodeIds=[oms_node.id])
    )


def test_get_node_ancestors_iris(
    mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker
):
    """Test get ancestor's iris."""

    sensemaker = build_sensemaker

    oms_node.classIri = "http://omsb/test/SmallTouringHelicopter"

    # mock getting the ontology classes
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/SmallTouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[OntologyClassOntologyClass.model_construct(iri="http://omsb/test/Helicopter")],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/Helicopter",
            defaultSymbolIdCode="10-0-0-01-0-0-00-000000-00-00",
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
                )
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[],
        ),
    ]

    iris = sensemaker.get_node_ancestors_iris(oms_node)
    assert iris == [
        "http://omsb/test/TouringHelicopter",
        "http://omsb/test/Helicopter",
        "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
    ]


def test_get_echelon(mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker):
    sensemaker = build_sensemaker

    sensemaker.get_echelon(oms_node)
    mock_oms_crud_tool.oms_client.attributes.assert_called_with(
        query=AttributeQuery(attributeIris=SETTINGS.mil_symbol_settings.echelon_iris, nodeIds=[oms_node.id])
    )


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_dimension_enrichment(
    mock_get_acm: mock.MagicMock,
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    build_sensemaker: MilSymbolSensemaker,
):
    """Test that the dimension is updated based on the parent IRIs"""

    sensemaker = build_sensemaker

    ### Mocks
    ## Mock getting acm
    mock_get_acm.return_value = DEFAULT_ACM

    # mock getting the ontology classes
    # UnknownHelicopter is not in dimension rules but Aircraft is so should use Air dimension values
    mock_oms_crud_tool.get_ontology_class = mock.MagicMock()
    mock_oms_crud_tool.get_ontology_class.side_effect = [
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/UnknownHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://omsb/test/TouringHelicopter")
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://omsb/test/TouringHelicopter",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
                )
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(
                    iri="http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"
                )
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            defaultSymbolIdCode=None,
            parentOntologyClasses=[
                OntologyClassOntologyClass.model_construct(iri="http://purl.obolibrary.org/obo/BFO_0000040")
            ],
        ),
        OntologyClassOntologyClass.model_construct(
            iri="http://purl.obolibrary.org/obo/BFO_0000040", defaultSymbolIdCode=None, parentOntologyClasses=[]
        ),
    ]

    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="hostile"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="damaged"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=[
            "http://omsb/test/TouringHelicopter",
            "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            "http://purl.obolibrary.org/obo/BFO_0000040",
        ]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))
    oms_node.symbolIdCode = None
    oms_node.classIri = "http://omsb/test/UnknownHelicopter"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols

    # The parent IRI makes sure we get the correct dimension of 01
    assert code_d.new_symbol_id_code == "10-0-6-01-3-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SHAD------*****"
    assert code_b.new_symbol_id_code == "SHAD------*****"


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.aac_client")
def test_acms(
    mock_aac_client: mock.MagicMock,
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    build_sensemaker: MilSymbolSensemaker,
    ts_acm: Dict,
):
    sensemaker = build_sensemaker

    # case 1
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true", acm=ts_acm
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(attribute_value="hostile"))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="damaged"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))
    oms_node.symbolIdCode = "10-0-0-30-0-0-32-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols
    assert code_d.new_symbol_id_code == "10-0-6-30-3-0-32-000000-00-00"
    assert code_c.new_symbol_id_code == "SHSD------*****"
    assert code_b.new_symbol_id_code == "SHSD------*****"
    mock_aac_client.get_acm_rollup.assert_any_call(
        [
            {"ACM": ts_acm},
            {"ACM": DEFAULT_ACM},
            {"ACM": DEFAULT_ACM},
            {"ACM": DEFAULT_ACM},
        ]
    )


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_controlling_affiliation_enrichment(
    mock_get_acm: AacClient, mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker
):
    """Test that the affiliation is updated based on the parent controlling nodes"""

    sensemaker = build_sensemaker

    ### Mocks
    ## Mock getting acm
    mock_get_acm.return_value = DEFAULT_ACM

    ## Mock API Calls in get_affiliation
    mock_oms_crud_tool.get_nodes = mock.MagicMock(
        return_value=NodesNodes.model_construct(data=[NodeNode.model_construct(id=uuid4())])
    )

    mock_oms_crud_tool.get_node_attribute_by_iri = mock.MagicMock(side_effect=[[], []])

    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"
        )
    )
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(attribute_value="damaged"))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=[
            "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            "http://purl.obolibrary.org/obo/BFO_0000040",
        ]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))

    ### Test non-derivative node doesn't get checked
    oms_node.symbolIdCode = "10-0-0-01-0-0-00-000000-00-00"
    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    assert symbols[0].new_symbol_id_code == "10-0-0-01-3-0-00-000000-00-00"
    assert symbols[1].new_symbol_id_code == "SPAD------*****"
    assert symbols[2].new_symbol_id_code == "SPAD------*****"
    mock_oms_crud_tool.get_nodes.assert_not_called()

    ### Test actually checking controlling node affiliations
    oms_node.tier = ObjectTier.DERIVATIVE

    # set no affiliation for the node but hostile for the parent node
    mock_oms_crud_tool.get_node_attribute_by_iri.side_effect = [[], [create_attribute(attribute_value="hostile")], []]

    oms_node.symbolIdCode = "10-0-0-00-0-0-00-000000-00-00"
    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols

    # The parent IRI makes sure we get the correct dimension of 01
    assert code_d.new_symbol_id_code == "10-0-6-01-3-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SHAD------*****"
    assert code_b.new_symbol_id_code == "SHAD------*****"
    mock_oms_crud_tool.get_nodes.assert_called_once()
