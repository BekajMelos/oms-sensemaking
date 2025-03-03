"""Military Symbol Sensemakers."""
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    Confidence,
    CreateAttributeInput,
    NodeNode,
    OntologyClassOntologyClass,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, FindingType, Sensemaker
from oms_sensemaking.mil_symbol.converters import to_2525c, to_2525d
from oms_sensemaking.mil_symbol.std_2525c import MilSymbol2525C
from oms_sensemaking.mil_symbol.std_2525d import MilSymbol2525D

LOGGER = logging.getLogger(__name__)


@dataclass
class SymbolCodeUpdate(FindingBase):
    """Represents a symbol code update"""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.MIL_SYMBOL_UPDATE)
    old_symbol_id_code: str
    new_symbol_id_code: str
    acm: Dict

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def get_acm(self) -> Dict:
        return self.acm


class MilSymbolSensemaker(Sensemaker):
    """
    A sensemaker for detecting duplicate nodes in omsb.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "mil_symbol" algorithm implementation.

    """

    def __init__(self, settings: Dict, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of MilSymbolSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = SETTINGS.mil_symbol_settings.model_dump()
        self.settings = settings
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, oms_node: NodeNode) -> List[SymbolCodeUpdate]:
        """
        Update a Node's symbol code based on its attributes and metadata

        :param oms_node: The node to analyze.
        :return: List of Mil Symbol Code updates
        """

        symbol_id_code = self.get_starting_symbol_id_code(oms_node)
        if not symbol_id_code:
            symbol_id_code = SETTINGS.mil_symbol_settings.default_2525d_code
            LOGGER.info(f"No default code for {oms_node.classIri}. Starting from default {symbol_id_code}")
        LOGGER.info(f"Initial symbol_id_code: {symbol_id_code}")

        code_2525c = None
        code_2525d = None

        trimmed_symbol_id_code = symbol_id_code.replace("-", "")
        if len(trimmed_symbol_id_code) == 20 and re.match(r'^([\d]{20})$', trimmed_symbol_id_code):
            code_2525d = MilSymbol2525D(trimmed_symbol_id_code, self.settings)
            code_2525c = to_2525c(code_2525d, self.settings)
        elif len(symbol_id_code) == 15:
            code_2525c = MilSymbol2525C(symbol_id_code, self.settings)
            code_2525d = to_2525d(code_2525c, self.settings)
        else:
            LOGGER.info(f"Unsupported SDIC for {symbol_id_code}")
            return []

        LOGGER.info(f"2525D before enrichment: {code_2525d.formatted_code}")
        LOGGER.info(f"2525C before enrichment: {code_2525c.formatted_code}")

        # Get OMS data to enrich codes
        context_attr = self.get_context(oms_node)
        affiliation_attr = self.get_affiliation(oms_node)
        status_attr = self.get_status(oms_node)

        code_2525d.enrich(context_attr, affiliation_attr, oms_node.classIri, status_attr)
        code_2525c.enrich(affiliation_attr, oms_node.classIri, status_attr)

        LOGGER.info(f"Enriched 2525C: {code_2525c.formatted_code}")
        LOGGER.info(f"Enriched 2525D: {code_2525d.formatted_code}")

        symbol_code_update_d = SymbolCodeUpdate(
            old_symbol_id_code=oms_node.symbolIdCode,
            new_symbol_id_code=code_2525d.formatted_code,
            acm=oms_node.acm
        )

        symbol_code_update_c = SymbolCodeUpdate(
            old_symbol_id_code=oms_node.symbolIdCode,
            new_symbol_id_code=code_2525c.formatted_code,
            acm=oms_node.acm
        )

        results: List[SymbolCodeUpdate] = [symbol_code_update_d, symbol_code_update_c]

        # We need to have used sourced attributes in order to publish
        if not code_2525d.source_ids.empty():
            source = code_2525d.source_ids.get()[1]
            self.publish_attributes(oms_node, results, source)

        return results

    def get_starting_symbol_id_code(self, oms_node: NodeNode) -> str:
        """
        Get the initial symbol id code, whether from the node itself, or its parents

        :param oms_node: Node with symbol id code to update
        :return: The starting symbol id code
        """
        symbol_id_code = oms_node.symbolIdCode
        if not symbol_id_code:
            LOGGER.debug(f"Node does not have symbolIdCode set. "
                         f"Getting default from omsb based on iri {oms_node.classIri}")
            symbol_id_code = self.get_default_symbol_id_code(oms_node.classIri)

        return symbol_id_code

    def get_default_symbol_id_code(self, iri: str) -> Optional[str]:
        """Given an iri, return the closest parent with a defaultSymbolIdCode

        :param iri: Iri to search for
        :return: Closest parent iri with a defaultSymbolIdCode
        """
        ontology_class: Optional[OntologyClassOntologyClass] = self.oms_crud_tool.get_ontology_class(iri=iri)
        if not ontology_class:
            return None

        current_symbol_id_code = ontology_class.defaultSymbolIdCode
        if current_symbol_id_code:
            return current_symbol_id_code

        if not ontology_class.parentOntologyClasses:
            return None

        # If multiple parent Iris, just get the first one
        super_class_iri: str = ontology_class.parentOntologyClasses[0].iri

        return self.get_default_symbol_id_code(super_class_iri)

    def get_context(self, oms_node: NodeNode) -> Optional[AttributeAttribute]:
        """Get context for this node. Find an attribute with exercise, reality, or simulation iri and a truthy value

        :param oms_node: Node to grab the context for
        :return: The matched IRI
        """

        context_attrs: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id,
            SETTINGS.mil_symbol_settings.is_reality_context_iris +
            SETTINGS.mil_symbol_settings.is_exercise_context_iris +
            SETTINGS.mil_symbol_settings.is_simulation_context_iris
        )

        if context_attrs:
            for context_attr in context_attrs:
                if context_attr.attributeValue.lower() == "true":
                    return context_attr

        return None

    def get_affiliation(self, oms_node: NodeNode) -> Optional[AttributeAttribute]:
        """Get affiliation/standard identity for this node.

        :param oms_node: Node to grab the affiliation for
        :return: The Node's standard identity
        """

        # TODO there could be multiple IRIs for affiliation

        affiliation_attr: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id,
            SETTINGS.mil_symbol_settings.affiliation_iris
            )

        if affiliation_attr:
            return affiliation_attr[0]

        return None

    def get_status(self, oms_node: NodeNode) -> Optional[AttributeAttribute]:
        """Get status for this node.

        :param oms_node: Node to grab the status for
        :return: The Node's status
        """
        status_attr: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id,
            SETTINGS.mil_symbol_settings.status_iris
        )

        if status_attr:
            return status_attr[0]

        return None

    def publish_attributes(self,
                           oms_node: NodeNode,
                           symbol_code_updates: List[SymbolCodeUpdate],
                           source_id: uuid.UUID) -> None:
        """
        Create and return duplicate finding objects from matched nodes

        :param oms_node: Node to associate attributes to
        :param symbol_code_updates: Symbol code updates
        :param source_id: Source Id to associate attributes to
        :return: None
        """

        for symbol_code_update in symbol_code_updates:

            attribute: CreateAttributeInput = CreateAttributeInput(
                tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                attributeType=AttributeType.STRING,
                attributeValue=symbol_code_update.new_symbol_id_code,
                confidence=Confidence.HIGH.value,
                acm=oms_node.acm,
                nodeId=oms_node.id,
                sourceId=source_id
            )
            self.oms_crud_tool.create_attribute(attribute)

        LOGGER.info(f"Mil Symbol Sensemaker updated symbol codes for {oms_node.id}")
