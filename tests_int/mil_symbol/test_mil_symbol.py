"""MilSymbol Sensemaker Integration Tests"""
from typing import List
from unittest import mock

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    Confidence,
    CreateAttributeInput,
    CreateNodeInput,
    NodeNode,
    ObjectTier,
)
from sqlalchemy import delete, select

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker, SymbolCodeUpdate
from oms_sensemaking.models.sensemaking import Finding, FindingType


def create_node(oms_crud_tool: OmsCrudTool, class_iri: str, symbol_id_code: str) -> NodeNode:

    create_node_input = CreateNodeInput(
        acm=DEFAULT_ACM,
        name="test node",
        tier=ObjectTier.PRIMARY,
        tags=["test"],
        classIri=class_iri,
        symbolIdCode=symbol_id_code,
        allegiance="AA"
    )
    node = oms_crud_tool.create_node(create_node_input)
    return node


def create_attribute(
        oms_node: NodeNode,
        attribute_iri: str,
        attribute_value: str,
        mock_source) -> AttributeAttribute:

    attr = AttributeAttribute.model_construct(
        attributeType=AttributeType.STRING,
        attributeValue=attribute_value,
        attributeIri=attribute_iri,
        acm=DEFAULT_ACM,
        sourceId=mock_source.id,
        confidence=Confidence.HIGH,
        nodeId=oms_node.id
    )
    return attr


def test_execute(mock_source, db, mil_symbol_rules):

    oms_crud_tool = OmsCrudTool()
    sensemaker = MilSymbolSensemaker(mil_symbol_rules, oms_crud_tool)

    # mock create_attribute
    oms_crud_tool.create_attribute = mock.MagicMock()

    # case 1
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
        "10-0-0-30-0-0-32-000000-00-00"
    )
    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "hostile", mock_source))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "damaged", mock_source))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(return_value=[])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 2

    # check that symbols exist in Findings table
    findings = db.execute(
        select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data["new_symbol_id_code"] == "10-0-6-30-3-0-32-000000-00-00"
    assert findings[1].finding_data["new_symbol_id_code"] == "SHSD------*****"

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id
            )
        )

    # clear findings
    findings = db.execute(delete(Finding))


    # case 2
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        "10-0-0-01-0-0-00-000000-00-00"
    )
    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction", "true", mock_source))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "suspect", mock_source))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "destroyed", mock_source))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=[
            "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            "http://purl.obolibrary.org/obo/BFO_0000040"
            ])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 2

    # check that symbols exist in Findings table
    findings = db.execute(
        select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data["new_symbol_id_code"] == "10-2-5-01-4-0-00-000000-00-00"
    assert findings[1].finding_data["new_symbol_id_code"] == "SSAX------*****"

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id
            )
        )

    # clear findings
    findings = db.execute(delete(Finding))

    # case 3
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft",
        "10-0-0-01-0-0-00-000000-00-00"
    )
    sensemaker.get_context = mock.MagicMock(return_value=create_attribute(
        oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source))
    sensemaker.get_affiliation = mock.MagicMock(return_value=create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "friendly", mock_source))
    sensemaker.get_status = mock.MagicMock(return_value=create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "present", mock_source))
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 2

    # check that symbols exist in Findings table
    findings = db.execute(
        select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data["new_symbol_id_code"] == "10-0-3-05-0-0-00-000000-00-00"
    assert findings[1].finding_data["new_symbol_id_code"] == "SFPP------*****"

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id
            )
        )

    # clear findings
    findings = db.execute(delete(Finding))
