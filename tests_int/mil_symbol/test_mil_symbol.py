"""MilSymbol Sensemaker Integration Tests"""

from typing import List, Optional
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    Confidence,
    CreateAttributeInput,
    CreateNodeInput,
    NodeNode,
    ObjectTier,
    RelationshipRelationship,
    SourceSource,
    UpdateNodeInput,
)
from sqlalchemy import select

from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker, SymbolCodeUpdate
from oms_sensemaking.models.sensemaking import Finding, FindingType


class FixtureHelper:
    def __init__(self, oms_crud_tool: OmsCrudTool, sensemaker: MilSymbolSensemaker) -> None:
        self.oms_crud_tool = oms_crud_tool
        self.sensemaker = sensemaker


def create_node(oms_crud_tool: OmsCrudTool, class_iri: str, symbol_id_code: str) -> NodeNode:
    create_node_input = CreateNodeInput(
        acm=DEFAULT_ACM,
        name="test node",
        tier=ObjectTier.PRIMARY,
        tags=["test"],
        classIri=class_iri,
        symbolIdCode=symbol_id_code,
        allegiance="AUS",
        labels=[],
    )
    node = oms_crud_tool.create_node(create_node_input)
    return node


def create_attribute(
    oms_node: NodeNode,
    attribute_iri: str,
    attribute_value: str,
    mock_source: SourceSource,
    tags: Optional[List[str]] = None,
) -> AttributeAttribute:
    attr = AttributeAttribute.model_construct(
        id=uuid4(),
        attributeType=AttributeType.STRING,
        attributeValue=attribute_value,
        attributeIri=attribute_iri,
        acm=DEFAULT_ACM,
        sourceId=mock_source.id,
        confidence=Confidence.HIGH,
        nodeId=oms_node.id,
        tags=tags,
    )
    return attr


@pytest.fixture
def build_helper(mil_symbol_rules):
    oms_crud_tool = OmsCrudTool()
    ontology_service = OntologyClient(oms_crud_tool)

    # mock create_attribute
    oms_crud_tool.create_attribute = mock.MagicMock()
    oms_crud_tool.update_node = mock.MagicMock()

    return FixtureHelper(oms_crud_tool, MilSymbolSensemaker(mil_symbol_rules, oms_crud_tool, ontology_service))


def test_execute(mock_source, db, build_helper):
    helper = build_helper
    oms_crud_tool = helper.oms_crud_tool
    sensemaker = helper.sensemaker

    # case 1
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
        "10-0-0-30-0-0-32-000000-00-00",
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "hostile", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "damaged", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(return_value=[])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 3
    new_id_codes_case1 = ["10-0-6-30-3-0-32-000000-00-00", "SHSD------*****", "SHSD------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case1)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )

    # case 2
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        "10-0-0-01-0-0-00-000000-00-00",
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(
            oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Restriction", "true", mock_source
        )
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "suspect", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "destroyed", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=[
            "http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle",
            "http://purl.obolibrary.org/obo/BFO_0000040",
        ]
    )

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 6
    new_id_codes_case2 = ["10-2-5-01-4-0-00-000000-00-00", "SSAX------*****", "SSAX------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case2)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )

    # case 3
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft",
        "10-0-0-01-0-0-00-000000-00-00",
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "friendly", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "present", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 9
    new_id_codes_case3 = ["10-0-3-05-0-0-00-000000-00-00", "SFPP------*****", "SFPP------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case3)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )

    # case 4 (Attribute Update)
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft",
        "10-0-0-01-0-0-00-000000-00-00",
    )

    oms_attribute = create_attribute(oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "neutral", mock_source)

    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=oms_attribute)
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "present", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )

    # test an Attribute being executed by the Sensemaker
    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_attribute)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 12
    new_id_codes_case4 = ["10-0-4-05-0-0-00-000000-00-00", "SNPP------*****", "SNPP------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case4)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )

    # case 5 (Ignore due to Tags from this Sensemaker)
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft",
        "10-0-0-01-0-0-00-000000-00-00",
    )

    oms_attribute = create_attribute(
        oms_node,
        SETTINGS.mil_symbol_settings.affiliation_iris[0],
        "neutral",
        mock_source,
        # The sensemaker should ignore Attribute creates/updates it wrote
        tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
    )

    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=oms_attribute)
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "present", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )

    # test an Attribute being executed by the Sensemaker
    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_attribute)
    assert len(symbols) == 0

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 12

    # case 6 (Ignore 'Icon' Attributes)
    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Spacecraft",
        "10-0-0-01-0-0-00-000000-00-00",
    )

    # ICON's are published by this Sensemaker so it doesn't need to process them
    oms_attribute = create_attribute(
        oms_node, SETTINGS.mil_symbol_settings.symbol_attribute_iri, "SNPP------*****", mock_source
    )

    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(return_value=oms_attribute)
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "present", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(
        return_value=["http://www.ontologyrepository.com/CommonCoreOntologies/Vehicle"]
    )

    # test an Attribute being executed by the Sensemaker
    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_attribute)
    assert len(symbols) == 0

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 12

    # case 7 (Wrong Input Type)
    oms_relationship = RelationshipRelationship.model_construct(
        name=SETTINGS.resolution_relationship_name,
        startNodeId=oms_node.id,
    )

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_relationship)
    assert len(symbols) == 0

    # check that symbols do not exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 12


def test_receive_c_correctly_create_and_enrich_b_and_d(mock_source, db, build_helper):
    helper = build_helper
    oms_crud_tool = helper.oms_crud_tool
    sensemaker = helper.sensemaker

    oms_node = create_node(
        oms_crud_tool, "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft", "SUSP------*****"
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "none specified", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "damaged", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(return_value=[])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 3
    new_id_codes_case = ["10-0-1-30-3-0-00-000000-00-00", "SUSD------*****", "SOSP------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )


def test_receive_d_correctly_create_and_enrich_b_and_c(mock_source, db, build_helper):
    helper = build_helper
    oms_crud_tool = helper.oms_crud_tool
    sensemaker = helper.sensemaker

    oms_node = create_node(
        oms_crud_tool,
        "http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
        "10-0-0-30-0-0-32-000000-00-00",
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "none specified", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "damaged", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(return_value=[])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 3
    new_id_codes_case = ["10-0-1-30-3-0-32-000000-00-00", "SUSD------*****", "SOSP------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )


def test_receive_b_correctly_create_and_enrich_c_and_d(mock_source, db, build_helper):
    helper = build_helper
    oms_crud_tool = helper.oms_crud_tool
    sensemaker = helper.sensemaker

    oms_node = create_node(
        oms_crud_tool, "http://www.ontologyrepository.com/CommonCoreOntologies/GroundVehicle", "SOGP------*****"
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "none specified", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "destroyed", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(return_value=[])

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 3
    new_id_codes_case = ["10-0-1-10-4-0-00-000000-00-00", "SUGX------*****", "SOGP------*****"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )


def test_echelon_enrichment(mock_source, db, build_helper):
    helper = build_helper
    oms_crud_tool = helper.oms_crud_tool
    sensemaker = helper.sensemaker

    oms_node = create_node(
        oms_crud_tool, "http://www.ontologyrepository.com/CommonCoreOntologies/GroundVehicle", "SOGP------*****"
    )
    sensemaker.get_context = mock.MagicMock(
        return_value=create_attribute(oms_node, "https://foundry.ai.mil/MIDB_GST/v1/Target_Vetted", "true", mock_source)
    )
    sensemaker.get_affiliation = mock.MagicMock(
        return_value=create_attribute(
            oms_node, SETTINGS.mil_symbol_settings.affiliation_iris[0], "none specified", mock_source
        )
    )
    sensemaker.get_status = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.status_iris[0], "destroyed", mock_source)
    )
    sensemaker.get_node_ancestors_iris = mock.MagicMock(return_value=[])
    sensemaker.get_echelon = mock.MagicMock(
        return_value=create_attribute(oms_node, SETTINGS.mil_symbol_settings.echelon_iris[0], "team", mock_source)
    )

    symbols: List[SymbolCodeUpdate] = sensemaker.execute(oms_node)
    assert len(symbols) == 3

    oms_crud_tool.update_node.assert_any_call(
        UpdateNodeInput(id=oms_node.id, symbolIdCode=symbols[1].new_symbol_id_code, labels=[SETTINGS.sm_enriched_label])
    )

    # check that symbols exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.MIL_SYMBOL_UPDATE.value)).scalars().all()
    )

    assert len(findings) == 3
    new_id_codes_case = ["10-0-1-10-4-0-11-000000-00-00", "SUGX------*A***", "SOGP------*A***"]
    assert all(any(s in f.finding_data["new_symbol_id_code"] for f in findings) for s in new_id_codes_case)

    for symbol in symbols:
        oms_crud_tool.create_attribute.assert_any_call(
            CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, sensemaker.version_string],
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol.new_symbol_id_code,
                attributeName="Icon",
                confidence=Confidence.HIGH.value,
                acm=symbol.acm,
                nodeId=oms_node.id,
                sourceId=mock_source.id,
            )
        )
