"""MilSymbol Sensemaker Unit Tests"""

from typing import Dict, List
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributesAttributes,
    MilSymbolAttributes,
    MilSymbolAttributesAffiliation,
    MilSymbolAttributesAffiliationData,
    MilSymbolAttributesContext,
    MilSymbolAttributesContextData,
    MilSymbolAttributesEchelon,
    MilSymbolAttributesStatus,
    MilSymbolAttributesStatusData,
    NodeNode,
    ObjectTier,
    OntologyClassOntologyClass,
)

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.exceptions import MilSymbolInvalidIdCharError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.get_attributes import GetMilSymbolAttributeFactory, GetMilSymbolAttributes
from oms_sensemaking.mil_symbol.sensemaker import MilSymAttrsPublisher, MilSymbolSensemaker, SymbolCodeUpdate


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
def attribute_retriever(mock_oms_crud_tool) -> GetMilSymbolAttributes:
    retriever = GetMilSymbolAttributeFactory(mock_oms_crud_tool).get_attribute_retriever(
        SETTINGS.mil_symbol_settings.mil_sym_attr_retriever
    )
    return retriever


@pytest.fixture
def build_sensemaker(
    mock_oms_crud_tool: OmsCrudTool, mil_symbol_rules: Dict, attribute_retriever: GetMilSymbolAttributes
):
    sensemaker = MilSymbolSensemaker(
        mil_symbol_rules, mock_oms_crud_tool, OntologyClient(mock_oms_crud_tool), attribute_retriever
    )
    return sensemaker


def attr_context_data(attribute_iri=None, attribute_value=None, acm=DEFAULT_ACM) -> MilSymbolAttributesContextData:
    context_data = MilSymbolAttributesContextData.model_construct(
        id=uuid4(), attributeIri=attribute_iri, attributeValue=attribute_value, sourceId=uuid4(), acm=acm
    )
    return context_data


def attr_affiliation_data(attribute_iri=None, attribute_value=None, acm=DEFAULT_ACM) -> MilSymbolAttributesContextData:
    affiliation_data = MilSymbolAttributesAffiliationData.model_construct(
        id=uuid4(), attributeIri=attribute_iri, attributeValue=attribute_value, sourceId=uuid4(), acm=acm
    )
    return affiliation_data


def attr_status_data(attribute_iri=None, attribute_value=None, acm=DEFAULT_ACM) -> MilSymbolAttributesContextData:
    status_data = MilSymbolAttributesStatusData.model_construct(
        id=uuid4(), attributeIri=attribute_iri, attributeValue=attribute_value, sourceId=uuid4(), acm=acm
    )
    return status_data


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
@mock.patch("oms_sensemaking.core.sensemakers.FindingWriter")
def test_process_data(
    mock_finding_writer: mock.MagicMock,
    mock_get_acm: AacClient,
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    build_sensemaker: MilSymbolSensemaker,
):
    sensemaker = build_sensemaker
    ### Mocks
    ## Mock getting acm
    mock_get_acm.return_value = DEFAULT_ACM
    ## Mock finding writer
    mock_finding_writer.return_value.save_findings.return_value = None

    # case 1
    sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"),
            attr_affiliation_data(attribute_value="hostile"),
            attr_status_data(attribute_value="damaged"),
            None,
        ]
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))
    oms_node.symbolIdCode = "10-0-0-30-0-0-32-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"

    symbols1: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols1) == 3
    code_d, code_c, code_b = symbols1
    assert code_d.new_symbol_id_code == "10-0-6-30-3-0-32-000000-00-00"
    assert code_c.new_symbol_id_code == "SHSD------*****"
    assert code_b.new_symbol_id_code == "SHSP------*****"

    # case 2
    sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(
                attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction", attribute_value="true"
            ),
            attr_affiliation_data(attribute_value="suspect"),
            attr_status_data(attribute_value="destroyed"),
            None,
        ]
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    oms_node.symbolIdCode = "10-0-0-01-0-0-00-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"

    symbols2: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols2) == 3
    code_d, code_c, code_b = symbols2
    assert code_d.new_symbol_id_code == "10-2-5-01-4-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SSAX------*****"
    assert code_b.new_symbol_id_code == "SSAP------*****"

    # case 3
    sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"),
            attr_affiliation_data(attribute_value="friendly"),
            attr_status_data(attribute_value="present"),
            None,
        ]
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    oms_node.symbolIdCode = "spzp------*****"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft"

    symbols3: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols3) == 3
    code_d, code_c, code_b = symbols3
    assert code_d.new_symbol_id_code == "10-0-3-05-0-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SFPP------*****"
    assert code_b.new_symbol_id_code == "SFPP------*****"


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_correct_updates_made_when_none_specified(
    mock_get_acm: AacClient, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker
):
    sensemaker = build_sensemaker
    mock_get_acm.return_value = DEFAULT_ACM
    sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"),
            attr_affiliation_data(attribute_value="none specified"),
            attr_status_data(attribute_value="present"),
            None,
        ]
    )
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


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
@mock.patch("oms_sensemaking.core.sensemakers.FindingWriter")
def test_dimension_enrichment(
    mock_finding_writer: mock.MagicMock,
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
    ## Mock finding writer
    mock_finding_writer.return_value.save_findings.return_value = None

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

    sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"),
            attr_affiliation_data(attribute_value="hostile"),
            attr_status_data(attribute_value="damaged"),
            None,
        ]
    )
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
    assert code_b.new_symbol_id_code == "SHAP------*****"


@mock.patch("oms_sensemaking.core.sensemakers.FindingWriter")
@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.aac_client")
def test_acms(
    mock_aac_client: mock.MagicMock,
    mock_finding_writer_class: mock.MagicMock,
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    build_sensemaker: MilSymbolSensemaker,
    ts_acm: Dict,
):
    mock_instance = mock_finding_writer_class.return_value
    mock_instance.save_findings.return_value = None
    sensemaker = build_sensemaker
    sensemaker._finding_writer = mock_instance

    # case 1
    sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(
                attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true", acm=ts_acm
            ),
            attr_affiliation_data(attribute_value="hostile"),
            attr_status_data(attribute_value="damaged"),
            None,
        ]
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))
    mock_aac_client.get_acm_rollup.return_value = {"ACM": ts_acm}
    oms_node.symbolIdCode = "10-0-0-30-0-0-32-000000-00-00"
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols
    assert code_d.new_symbol_id_code == "10-0-6-30-3-0-32-000000-00-00"
    assert code_c.new_symbol_id_code == "SHSD------*****"
    assert code_b.new_symbol_id_code == "SHSP------*****"
    mock_aac_client.get_acm_rollup.assert_any_call(
        [
            {"ACM": ts_acm},
            {"ACM": DEFAULT_ACM},
            {"ACM": DEFAULT_ACM},
            {"ACM": DEFAULT_ACM},
        ]
    )


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
@mock.patch("oms_sensemaking.core.sensemakers.FindingWriter")
def test_affiliation_fallback_to_parent_is_triggered(
    mock_finding_writer: mock.MagicMock,
    mock_get_acm: AacClient,
    mock_oms_crud_tool: OmsCrudTool,
    oms_node: NodeNode,
    build_sensemaker: MilSymbolSensemaker,
):
    """Test that affiliation enrichment falls back to parent affiliation."""

    mock_get_acm.return_value = DEFAULT_ACM
    mock_finding_writer.return_value.save_findings.return_value = None

    sensemaker = build_sensemaker

    msa = MilSymbolAttributes.model_construct()
    msa.affiliation = MilSymbolAttributesAffiliation.model_construct(data=None)
    msa.context = MilSymbolAttributesContext.model_construct(
        data=[
            attr_context_data(attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true")
        ]
    )
    msa.status = MilSymbolAttributesStatus.model_construct(data=[attr_status_data(attribute_value="damaged")])
    msa.echelon = MilSymbolAttributesEchelon.model_construct(data=None)
    sensemaker._attribute_retriever.oms_crud_tool.get_mil_symbol_attr = mock.MagicMock(return_value=msa)

    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=[
            "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            "http://purl.obolibrary.org/obo/BFO_0000040",
        ]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))

    # Mock parent affiliation logic
    mock_parent_affiliation = attr_affiliation_data(attribute_value="hostile")
    sensemaker._attribute_retriever.get_affiliation_of_parent_nodes = mock.MagicMock(
        return_value=mock_parent_affiliation
    )

    oms_node.tier = ObjectTier.DERIVATIVE
    oms_node.symbolIdCode = "10-0-0-00-0-0-00-000000-00-00"

    enrichment_attrs = sensemaker._attribute_retriever.get_all_mil_sym_attrs_for_enrichment(oms_node)

    sensemaker._attribute_retriever.get_affiliation_of_parent_nodes.assert_called_once_with(oms_node)
    assert enrichment_attrs[1].attributeValue == "hostile"
    assert enrichment_attrs[0].attributeValue == "true"
    assert enrichment_attrs[2].attributeValue == "damaged"
    assert enrichment_attrs[3] is None

    symbols: List[SymbolCodeUpdate] = sensemaker.process_data(oms_node)
    assert len(symbols) == 3
    code_d, code_c, code_b = symbols

    # The parent IRI makes sure we get the correct dimension of 01
    assert code_d.new_symbol_id_code == "10-0-6-01-3-0-00-000000-00-00"
    assert code_c.new_symbol_id_code == "SHAD------*****"
    assert code_b.new_symbol_id_code == "SHAP------*****"


@pytest.mark.parametrize(
    "tags, expected_value, message",
    [
        ([], False, "expected untagged object to not have mil symbol tags"),
        (
            SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
            True,
            "expected object tagged with mil symbol tags to have the mil symbol tags",
        ),
    ],
)
def test_has_mil_symbol_sensemaker_tags(tags: list[str], expected_value, message: str):
    actual = MilSymbolSensemaker.has_mil_symbol_sensemaker_tags(tags)
    assert actual == expected_value, message


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_milsym_invalid_char_error(
    mock_get_acm: AacClient, mock_oms_crud_tool: OmsCrudTool, oms_node: NodeNode, build_sensemaker: MilSymbolSensemaker
):
    sensemaker = build_sensemaker
    ### Mocks
    ## Mock getting acm
    mock_get_acm.return_value = DEFAULT_ACM

    # case 1
    sensemaker.get_all_mil_sym_attrs_for_enrichment = mock.MagicMock(
        return_value=[
            attr_context_data(attribute_iri="https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", attribute_value="true"),
            attr_affiliation_data(attribute_value="hostile"),
            attr_status_data(attribute_value="damaged"),
            None,
        ]
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )
    mock_oms_crud_tool.get_attributes = mock.MagicMock(return_value=AttributesAttributes(rollupAcm=None, data=[]))
    oms_node.symbolIdCode = "10-0-0-89-0-0-32-000000-00-00"  # 89 is invalid
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft"

    with pytest.raises(MilSymbolInvalidIdCharError) as exc_info:
        sensemaker.process_data(oms_node)
    assert "is invalid and cannot be processed" in str(exc_info.value)


def test_mil_sym_attr_publisher_init(mock_oms_crud_tool, build_sensemaker, oms_node):
    sensemaker = build_sensemaker
    mock_symbol_code_updates = mock.MagicMock(spec=list[SymbolCodeUpdate])
    mock_source = mock.MagicMock()
    mock_source.id = uuid4()

    publisher = MilSymAttrsPublisher(
        mock_oms_crud_tool, sensemaker.version_string, oms_node, mock_symbol_code_updates, mock_source.id
    )
    assert isinstance(publisher.oms_crud_tool, OmsCrudTool)
    assert publisher.version == "v1.0.0"
    assert publisher.oms_node == oms_node
    assert publisher.source_id == mock_source.id


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_mil_sym_attr_publisher_create_attr_inputs(mock_get_acm, mock_oms_crud_tool, build_sensemaker, oms_node):
    mock_get_acm.return_value = DEFAULT_ACM

    sensemaker = build_sensemaker
    symcodeupdate1 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate2 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate3 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate1.id_type = "D"
    symcodeupdate2.id_type = "C"
    symcodeupdate3.id_type = "B"
    symcodeupdate1.new_symbol_id_code = "new D"
    symcodeupdate2.new_symbol_id_code = "new C"
    symcodeupdate3.new_symbol_id_code = "new B"
    mock_symbol_code_updates = [symcodeupdate1, symcodeupdate2, symcodeupdate3]

    mock_source = mock.MagicMock()
    mock_source.id = uuid4()

    publisher = MilSymAttrsPublisher(
        mock_oms_crud_tool, sensemaker.version_string, oms_node, mock_symbol_code_updates, mock_source.id
    )
    res = publisher.create_attribute_inputs(
        sensemaker.version_string, oms_node, mock_symbol_code_updates, mock_source.id
    )
    assert len(res) == 3
    assert res[0].attributeValue == "new D"
    assert res[1].attributeValue == "new C"
    assert res[2].attributeValue == "new B"


@mock.patch("oms_sensemaking.mil_symbol.mil_symbol_std.MilSymbol.get_acm")
def test_mil_sym_attr_publisher_publish(mock_get_acm, mock_oms_crud_tool, build_sensemaker, oms_node):
    mock_get_acm.return_value = DEFAULT_ACM

    sensemaker = build_sensemaker
    symcodeupdate1 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate2 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate3 = mock.MagicMock(spec=SymbolCodeUpdate)
    symcodeupdate1.id_type = "D"
    symcodeupdate2.id_type = "C"
    symcodeupdate3.id_type = "B"
    symcodeupdate1.new_symbol_id_code = "new D"
    symcodeupdate2.new_symbol_id_code = "new C"
    symcodeupdate3.new_symbol_id_code = "new B"
    mock_symbol_code_updates = [symcodeupdate1, symcodeupdate2, symcodeupdate3]

    mock_source = mock.MagicMock()
    mock_source.id = uuid4()

    publisher = MilSymAttrsPublisher(
        mock_oms_crud_tool, sensemaker.version_string, oms_node, mock_symbol_code_updates, mock_source.id
    )
    res = publisher.create_attribute_inputs(
        sensemaker.version_string, oms_node, mock_symbol_code_updates, mock_source.id
    )
    attrs = publisher.publish_mil_sym_attrs()

    mock_oms_crud_tool.oms_client.create_mil_sym_attributes.assert_called_once_with(res[0], res[1], res[2])
    assert len(attrs) == 3
