"""Military Symbol Sensemakers."""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
    AttributeType,
    Confidence,
    CreateAttributeCreateAttribute,
    CreateAttributeInput,
    CreateNodeCreateNode,
    NodeNode,
    NodeQuery,
    NodeRelationshipQuery,
    NodeRelationshipSubQuery,
    NodesNodes,
    ObjectTier,
    RelationshipDirection,
    RestoreAttributeRestoreAttribute,
    RestoreNodeRestoreNode,
    UpdateAttributeInput,
    UpdateAttributeUpdateAttribute,
    UpdateNodeInput,
    UpdateNodeUpdateNode,
)

from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, FindingType, Sensemaker
from oms_sensemaking.mil_symbol.converters import to_2525b, to_2525c, to_2525d
from oms_sensemaking.mil_symbol.mil_symbol_maker import MilSymbolMaker
from oms_sensemaking.mil_symbol.std_2525b import MilSymbol2525B
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

    def __init__(self, settings: Dict, oms_crud_tool: OmsCrudTool, ontology_service: OntologyService) -> None:
        """Create a new instance of MilSymbolSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = SETTINGS.mil_symbol_settings.model_dump()
        self.settings = settings
        self.oms_crud_tool = oms_crud_tool
        self._ontology_service = ontology_service

    def process_data(
        self, oms_object: AttributeAttribute | NodeNode, config: dict | None = None
    ) -> List[SymbolCodeUpdate]:
        """
        Update a Node's symbol code based on its attributes and metadata

        :param oms_object: The attribute or node to analyze.
        :return: List of Mil Symbol Code updates
        """

        if self.is_attribute_to_ignore(oms_object):
            return []
        oms_node = self.get_node_from_input(oms_object)

        if oms_node is None:
            return []

        symbol_id_code = self.get_starting_symbol_id_code(oms_object, oms_node)
        if not symbol_id_code:
            symbol_id_code = SETTINGS.mil_symbol_settings.default_2525d_code
            LOGGER.info(f"No default code for {oms_node.classIri}. Starting from default {symbol_id_code}")
        LOGGER.info(f"Initial symbol_id_code: {symbol_id_code}")

        code_2525b = None
        code_2525c = None
        code_2525d = None

        mil_symbol = MilSymbolMaker.make(symbol_id_code, self.settings)

        if isinstance(mil_symbol, MilSymbol2525D):
            code_2525d = mil_symbol
            code_2525c = to_2525c(code_2525d, self.settings)
            code_2525b = to_2525b(code_2525c, self.settings)
        elif isinstance(mil_symbol, MilSymbol2525C):
            code_2525c = mil_symbol
            code_2525b = to_2525b(code_2525c, self.settings)
            code_2525d = to_2525d(code_2525c, self.settings)
        elif isinstance(mil_symbol, MilSymbol2525B):
            code_2525b = mil_symbol
            code_2525c = to_2525c(code_2525b, self.settings)
            code_2525d = to_2525d(code_2525c, self.settings)
        else:
            return []

        # use this to compare codes before and after enrichment to determine if we need to publish
        before_enrich_2525d = code_2525d.formatted_code

        LOGGER.info(f"Parsed 2525D for {oms_node.id}")
        LOGGER.info(f"Parsed 2525C for {oms_node.id}")
        LOGGER.info(f"Parsed 2525B for {oms_node.id}")

        # Get OMS data to enrich codes
        context_attr = self.get_context(oms_node)
        affiliation_attr = self.get_affiliation(oms_node)
        status_attr = self.get_status(oms_node)
        ancestor_iris = self.get_node_ancestors_iris(oms_node)
        echelon_attr = self.get_echelon(oms_node)

        code_2525d.enrich(context_attr, affiliation_attr, oms_node, ancestor_iris, status_attr, echelon_attr)
        code_2525c.enrich(affiliation_attr, oms_node, ancestor_iris, status_attr, echelon_attr)
        code_2525b.enrich(affiliation_attr, oms_node, ancestor_iris, status_attr, echelon_attr)

        LOGGER.info(f"Enriched 2525B for {oms_node.id}")
        LOGGER.info(f"Enriched 2525C for {oms_node.id}")
        LOGGER.info(f"Enriched 2525D for {oms_node.id}")

        symbol_code_update_d = SymbolCodeUpdate(
            old_symbol_id_code=oms_node.symbolIdCode,
            new_symbol_id_code=code_2525d.formatted_code,
            acm=code_2525d.get_acm(),
        )
        symbol_code_update_c = SymbolCodeUpdate(
            old_symbol_id_code=oms_node.symbolIdCode,
            new_symbol_id_code=code_2525c.formatted_code,
            acm=code_2525c.get_acm(),
        )

        symbol_code_update_b = SymbolCodeUpdate(
            old_symbol_id_code=oms_node.symbolIdCode,
            new_symbol_id_code=code_2525b.formatted_code,
            acm=code_2525c.get_acm(),
        )

        results: List[SymbolCodeUpdate] = [symbol_code_update_d, symbol_code_update_c, symbol_code_update_b]

        self.update_oms_node(oms_node, code_2525c.code)

        # We need to have used sourced attributes in order to publish
        # And only publish if there was a change in the symbol
        if not code_2525d.source_ids.empty() and symbol_code_update_d.new_symbol_id_code != before_enrich_2525d:
            source = code_2525d.source_ids.get()[1]
            self.publish_attributes(oms_node, results, source)

        return results

    def get_starting_symbol_id_code(self, oms_object: AttributeAttribute | NodeNode, oms_node: NodeNode) -> str:
        """
        Get the initial symbol id code, with the priority order Attribute -> Node.symbolIdCode -> derivedFrom(classIri)

        :param oms_object: Attribute or Node with symbold id code
        :param oms_node: Node with symbol id code to update
        :return: The starting symbol id code
        """
        if self.is_attribute(oms_object) and (
            oms_object.attributeIri in SETTINGS.mil_symbol_settings.attribute_code_iris
        ):
            symbol_id_code = oms_object.attributeValue
        else:
            symbol_id_code = oms_node.symbolIdCode
        if not symbol_id_code:
            LOGGER.debug(
                f"Node and Attribute do not have a symbol to use for the symbol_id_code."
                f"Getting default from omsb based on iri {oms_node.classIri}"
            )
            symbol_id_code = self.get_default_symbol_id_code(oms_node.classIri)

        return symbol_id_code

    def get_default_symbol_id_code(self, iri: str) -> Optional[str]:
        """Given an iri, return the closest parent with a defaultSymbolIdCode

        :param iri: Iri to search for
        :return: Closest parent iri with a defaultSymbolIdCode
        """
        return self._ontology_service.get_default_symbol_id_code(iri)

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

    def _get_hierarchical_parent_node(self, oms_node: NodeNode) -> NodesNodes:
        """Get the parent node according to a Controls or ControlledBy relationship"""
        return self.oms_crud_tool.get_nodes(
            NodeQuery(
                relationships=NodeRelationshipQuery(
                    or_=[
                        NodeRelationshipQuery(
                            hasMatch=NodeRelationshipSubQuery(
                                objectPropertyIris=SETTINGS.mil_symbol_settings.affiliation_controlled_by_iris,
                                relatedNodeIds=[oms_node.id],
                                direction=RelationshipDirection.OUTGOING,
                            )
                        ),
                        NodeRelationshipQuery(
                            hasMatch=NodeRelationshipSubQuery(
                                objectPropertyIris=SETTINGS.mil_symbol_settings.affiliation_controls_iris,
                                relatedNodeIds=[oms_node.id],
                                direction=RelationshipDirection.INCOMING,
                            )
                        ),
                    ]
                )
            )
        )

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

    def get_node_ancestors_iris(self, oms_node: NodeNode) -> List[str]:
        """Get ancestor's iris.

        :param oms_node: Node to grab the status for
        :return: The Node's ancestor's iri list
        """
        return self._ontology_service.mil_symbol_get_node_ancestors_iris(oms_node)

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

    def publish_attributes(
        self, oms_node: NodeNode, symbol_code_updates: List[SymbolCodeUpdate], source_id: uuid.UUID
    ) -> None:
        """
        Create and return duplicate finding objects from matched nodes

        :param oms_node: Node to associate attributes to
        :param symbol_code_updates: Symbol code updates
        :param source_id: Source Id to associate attributes to
        :return: None
        """

        # to avoid having more than two Icon attributes (one 2525C, one 2525D), first check
        # for existing Icon attributes (based on the IRI this Sensemaker publishes).
        # Update if they exist, otherwise create new ones
        attribute_query = AttributeQuery(
            nodeIds=[oms_node.id],
            attributeIris=[SETTINGS.mil_symbol_settings.symbol_attribute_iri],
            tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
        )
        attributes = self.oms_crud_tool.get_attributes(attribute_query)
        if attributes and attributes.data:
            try:
                for existing_icon, symbol_code_update in zip(attributes.data, symbol_code_updates, strict=True):
                    update_attribute_input = UpdateAttributeInput(
                        id=existing_icon.id, attributeValue=symbol_code_update.new_symbol_id_code
                    )
                    self.oms_crud_tool.update_attribute(update_attribute_input)
            except ValueError:
                LOGGER.exception("Unable to update Icon Attributes.")
                raise
        else:
            for symbol_code_update in symbol_code_updates:
                attribute: CreateAttributeInput = CreateAttributeInput(
                    tags=SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags,
                    labels=[SETTINGS.sm_inferenced_label, SETTINGS.mil_sym_sm_label, self.version_string],
                    attributeIri=SETTINGS.mil_symbol_settings.symbol_attribute_iri,
                    attributeType=AttributeType.STRING,
                    attributeValue=symbol_code_update.new_symbol_id_code,
                    confidence=Confidence.HIGH.value,
                    acm=symbol_code_update.get_acm(),
                    nodeId=oms_node.id,
                    sourceId=source_id,
                )
                self.oms_crud_tool.create_attribute(attribute)

        LOGGER.info(f"Mil Symbol Sensemaker updated symbol codes for {oms_node.id}")

    def update_oms_node(self, oms_node: NodeNode, code: str) -> None:
        """Update the Oms Node with the new code

        :param oms_node: Node to update
        :param code: code to set for symbolIdCode
        :return: None
        """
        node_labels = oms_node.labels
        if node_labels is None:
            node_labels = []
        node_labels.append(SETTINGS.sm_enriched_label)
        update_node_input = UpdateNodeInput(id=oms_node.id, symbolIdCode=code, labels=node_labels)
        self.oms_crud_tool.update_node(update_node_input)

    def get_node_from_input(self, oms_object: AttributeAttribute | NodeNode) -> Optional[NodeNode]:
        """Get an OMS Node based on the input type

        :param oms_object: The Node to return or the Attribute used to find the Node
        :return: An OMS Node
        """
        if self.is_node(oms_object):
            LOGGER.info("Checking for MilSymbol enrichment based on Node input.")
            return oms_object
        elif self.is_attribute(oms_object):
            LOGGER.info("Checking for MilSymbol enrichment based on Attribute input.")
            LOGGER.info("Getting linked Node from Attribute nodeId.")
            if oms_object.nodeId is None:
                LOGGER.warning("Node not found. Unable to check for MilSymbol enrichment.")
                return None

            return self.oms_crud_tool.get_node(oms_object.nodeId)
        else:
            LOGGER.warning(f"Unexpected class type processed: {type(oms_object)}")
            return None

    def is_node(self, oms_object: NodeNode | AttributeAttribute) -> bool:
        """Check if the input is a NodeNode or object that has same properties

        :param oms_object: The object to check against Node properties
        :return: bool
        """

        return isinstance(oms_object, NodeNode | CreateNodeCreateNode | RestoreNodeRestoreNode | UpdateNodeUpdateNode)

    def is_attribute(self, oms_object: NodeNode | AttributeAttribute) -> bool:
        """Check if the input is an AttributeAttribute or object that has same properties

        :param oms_object: The object to check against Attribute properties
        :return: bool
        """

        return isinstance(
            oms_object,
            AttributeAttribute
            | CreateAttributeCreateAttribute
            | RestoreAttributeRestoreAttribute
            | UpdateAttributeUpdateAttribute,
        )

    def has_mil_symbol_sensemaker_tags(self, tags: List[str]):
        """
        Checks to see if an attribute has been tagged by this Sensemaker.

        :param tags: List of strings representing the tags of the attribute
        :return: boolean
        """

        if not tags:
            return False

        set_tags = set([t.lower() for t in tags])
        set_mil_symbol_tags = set([t.lower() for t in SETTINGS.mil_symbol_settings.mil_symbol_sensemaker_tags])
        return bool(set_tags.intersection(set_mil_symbol_tags))

    def is_attribute_to_ignore(self, oms_object: NodeNode | AttributeAttribute):
        """
        Checks to see if an attribute should be processed by this Sensemaker.
        Attributes that have the same IRI as the one this Sensemaker publishes
        or have already been tagged by this Sensemaker should be ignored.

        :param tags: List of strings representing the tags of the attribute
        :return: boolean
        """

        if self.is_attribute(oms_object) and (
            SETTINGS.mil_symbol_settings.symbol_attribute_iri in oms_object.attributeIri
            or self.has_mil_symbol_sensemaker_tags(oms_object.tags)
        ):
            LOGGER.info(f"MilSymbolSensemaker ignoring attribute it may have published: {oms_object.id}")
            return True
        return False
