"""Military Symbol Sensemakers."""

import logging
from typing import List, Optional, Protocol

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    MilSymbolAttributeFields,
    NodeNode,
    NodesNodes,
    ObjectTier,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER = logging.getLogger(__name__)


class GetMilSymbolAttributes(Protocol):
    def get_all_mil_sym_attrs_for_enrichment(self, oms_node: NodeNode):
        pass


class GetAllAttributesAtOnce(GetMilSymbolAttributes):
    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        self.oms_crud_tool = oms_crud_tool

    def get_all_mil_sym_attrs_for_enrichment(self, oms_node: NodeNode) -> list[None | MilSymbolAttributeFields]:
        enrichment_attributes: list[None | MilSymbolAttributeFields] = [None] * 4
        context_iris = (
            SETTINGS.mil_symbol_settings.is_exercise_context_iris
            + SETTINGS.mil_symbol_settings.is_reality_context_iris
            + SETTINGS.mil_symbol_settings.is_simulation_context_iris
        )
        all_attributes = self.oms_crud_tool.get_mil_symbol_attr(
            oms_node.id,
            SETTINGS.mil_symbol_settings.affiliation_iris,
            context_iris,
            SETTINGS.mil_symbol_settings.status_iris,
            SETTINGS.mil_symbol_settings.echelon_iris,
        )
        # Context logic
        context_data = all_attributes.context.data
        if context_data:
            for attr in context_data:
                if attr.attributeValue.lower() == "true":
                    enrichment_attributes[0] = attr
        # Affiliation logic
        affiliation_data = all_attributes.affiliation.data
        not_derivative = None
        if affiliation_data:
            enrichment_attributes[1] = affiliation_data[0]
        elif enrichment_attributes[1] is None and oms_node.tier != ObjectTier.DERIVATIVE:
            not_derivative = True
        elif enrichment_attributes[1] is None and not_derivative is None:
            enrichment_attributes[1] = self.get_affiliation_of_parent_nodes(oms_node)
        # Status logic
        status_data = all_attributes.status.data
        if status_data:
            enrichment_attributes[2] = status_data[0]
        # Echelon logic
        echelon_data = all_attributes.echelon.data
        if echelon_data:
            enrichment_attributes[3] = echelon_data[0]
        return enrichment_attributes


class SequentialGetAllAttributes(GetMilSymbolAttributes):
    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        self.oms_crud_tool = oms_crud_tool

    def get_all_mil_sym_attrs_for_enrichment(self, oms_node: NodeNode) -> list[None | MilSymbolAttributeFields]:
        context = self.get_context(oms_node)
        affiliation = self.get_affiliation(oms_node)
        status = self.get_status(oms_node)
        echelon = self.get_echelon(oms_node)
        return [context, affiliation, status, echelon]

    def get_context(self, oms_node: NodeNode) -> Optional[AttributeAttribute]:
        """Get context for this node. Find an attribute with exercise, reality, or simulation iri and a truthy value

        :param oms_node: Node to grab the context for
        :return: The matched IRI
        """

        context_attrs: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id,
            SETTINGS.mil_symbol_settings.is_reality_context_iris
            + SETTINGS.mil_symbol_settings.is_exercise_context_iris
            + SETTINGS.mil_symbol_settings.is_simulation_context_iris,
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

        affiliation_attrs: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id, SETTINGS.mil_symbol_settings.affiliation_iris
        )

        if affiliation_attrs:
            return affiliation_attrs[0]

        if oms_node.tier != ObjectTier.DERIVATIVE:
            return None

        LOGGER.debug("Affiliation code is still unknown. Checking ancestor related controlling nodes")

        # look for parent relationship
        # TODO: we don't actually care about parentNode data,
        # we should try to find a way to just get the nodeId and affiliation
        parent_nodes: NodesNodes = self._get_hierarchical_parent_node(oms_node)

        if not parent_nodes.data:
            return None

        for node in parent_nodes.data:
            parent_affiliation_attrs: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
                node.id, SETTINGS.mil_symbol_settings.affiliation_iris
            )

            if parent_affiliation_attrs:
                return parent_affiliation_attrs[0]

        return None

    def get_status(self, oms_node: NodeNode) -> Optional[AttributeAttribute]:
        """Get status for this node.

        :param oms_node: Node to grab the status for
        :return: The Node's status
        """
        status_attr: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id, SETTINGS.mil_symbol_settings.status_iris
        )

        if status_attr:
            return status_attr[0]

        return None

    def get_echelon(self, oms_node: NodeNode) -> Optional[AttributeAttribute]:
        """
        Get echelon for this node.

        :param oms_node: Node to get the echelon
        :return: The node's echelon
        """
        echelon_attr: List[AttributeAttribute] = self.oms_crud_tool.get_node_attribute_by_iri(
            oms_node.id, SETTINGS.mil_symbol_settings.echelon_iris
        )

        if echelon_attr:
            return echelon_attr[0]

        return None


class GetMilSymbolAttributeFactory:
    def __init__(self, oms_crud_tool: OmsCrudTool):
        self.oms_crud_tool = oms_crud_tool

    def get_attribute_retriever(self, retriver_type: str):
        match retriver_type:
            case "Sequential":
                return SequentialGetAllAttributes(self.oms_crud_tool)
            case "AllAtOnce":
                return GetAllAttributesAtOnce(self.oms_crud_tool)
            case _:
                raise ValueError("Invalid Mil Symol Attribute Retriever")
