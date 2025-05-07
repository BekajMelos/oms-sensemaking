"""Resolution Sensemakers."""

import copy
import logging
from dataclasses import dataclass, field
from itertools import chain
from uuid import UUID

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    CreateRelationshipInput,
    NodeAttributeQuery,
    NodeAttributeSubQuery,
    NodeNode,
    NodeQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
    StringQuery,
)
from oms_sdk.generated.generated_graphql_client.enums import Confidence

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.models.sensemaking import FindingType

LOGGER = logging.getLogger(__name__)


@dataclass
class DupFinding(FindingBase):
    """Represents a Duplicate Node Finding."""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.RESOLUTION_DUPLICATE)
    start_node_id: UUID
    end_node_id: UUID
    acm: dict

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def get_acm(self) -> dict:
        return self.acm


class ResolutionSensemaker(Sensemaker):
    """
    A sensemaker for detecting duplicate nodes in omsb.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Update making duplicate object checks configurable
    - Initial "resolution" algorithm implementation.

    """

    def __init__(self, duplicate_object_iris, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of ResolutionSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}
        self.oms_crud_tool = oms_crud_tool
        self.duplicate_object_iris = duplicate_object_iris

    def process_data(self, attribute: AttributeAttribute, config: dict | None = None) -> list[DupFinding]:
        """
        Determine if a created Node is the same as an existing note and suggest that they are merged

        :param attribute: The attribute to analyze.
        :return: list[DupFinding] List of duplicates found
        """
        LOGGER.info("Running Resolution Sensemaker")
        LOGGER.debug(f"{attribute.attributeIri}: {attribute.attributeValue}")

        results = []

        criterion: list[AttributeAttribute] = self.meets_criteria(attribute)
        if criterion:
            dups: list[NodeNode] = self.find_duplicates(criterion)
            dup_findings: list[DupFinding] = self.create_duplicate_findings(attribute, dups)
            results.extend(dup_findings)

        return results

    def meets_criteria(self, attribute: AttributeAttribute) -> list[AttributeAttribute]:
        """
        Gather the criteria needed to check for duplicates in OMSB.

        :param attribute: Initial OMSB Attribute Object
        :return: List of OMSB Attributes to look for

        """
        current_node_id = attribute.nodeId
        # Attribute doesn't point to a node
        if not current_node_id:
            return []
        
        current_iri = attribute.attributeIri
        all_attribute_iris = set(chain.from_iterable(self.duplicate_object_iris.values()))
        # Attribute not in relevant IRIs list
        if current_iri not in all_attribute_iris:
            return []

        duplicate_object_attributes = [attribute]
        class_iri = self.oms_crud_tool.get_node(current_node_id).classIri

        already_ran = self.has_already_ran(current_node_id)
        object_class_in_config = class_iri in self.duplicate_object_iris
        if object_class_in_config:
            duplicate_identifiers = self.duplicate_object_iris[class_iri]
            attribute_in_duplicate_identifiers = attribute.attributeIri in duplicate_identifiers

        if not object_class_in_config or not attribute_in_duplicate_identifiers or already_ran:
            return []

        # Get this nodes info and make sure we satisfy the requirements
        if len(duplicate_identifiers) > 1:
            other_iris: list[str] = copy.copy(duplicate_identifiers)
            other_iris.remove(current_iri)
            duplicate_object_attributes.extend(
                self.oms_crud_tool.get_node_attribute_by_iri(attribute.nodeId, other_iris)
            )

            if len(duplicate_object_attributes) != len(duplicate_identifiers):
                LOGGER.debug("Node does not have all required fields for Duplicate Object Matching. Ignoring.")
                return []

        return duplicate_object_attributes

    def create_duplicate_findings(self, attribute: AttributeAttribute, nodes: list[NodeNode]) -> list[DupFinding]:
        """
        Create and return duplicate finding objects from matched nodes

        :param attribute: Original attribute being matched on
        :param nodes: Matched nodes
        :return: List of DupFinding objects of matches
        """

        current_node_id = attribute.nodeId
        dups = []

        for node in nodes:
            # Ignore the node we're currently looking at
            if node.id == current_node_id:
                continue

            dup = DupFinding(start_node_id=current_node_id, end_node_id=node.id, acm=node.acm)
            dups.append(dup)

            rel: CreateRelationshipInput = CreateRelationshipInput(
                name=SETTINGS.resolution_relationship_name,
                tags=[SETTINGS.resolution_sensemaker_tag],
                labels=[SETTINGS.sm_inferenced_label, SETTINGS.res_sm_label, self.version_string],
                startNodeId=current_node_id,
                endNodeId=node.id,
                confidence=Confidence.HIGH.value,
                sourceId=attribute.sourceId,
                acm=attribute.acm,
                objectPropertyIri=SETTINGS.resolution_relationship_iri,
            )
            self.oms_crud_tool.create_relationship(rel)
            LOGGER.info(f"Resolution Sensemaker found duplicates {current_node_id}, {node.id}")

        return dups

    def has_already_ran(self, current_node_id: UUID) -> bool:
        """
        Deteremine if this check has already run and the nodes have already been tagged

        :param current_node_id: The node id we're checking for duplicates against
        :return: boolean indicating whether this check has run or not
        """

        query: RelationshipQuery = RelationshipQuery(
            name=StringQuery(equals=SETTINGS.resolution_relationship_name, ignoreCase=True),
            nodes=RelationshipNodeQuery(startNodeIds=[current_node_id]),
        )

        existing_relationships = self.oms_crud_tool.get_relationships(query)
        if existing_relationships and len(existing_relationships.data) > 0:
            LOGGER.debug("Sensemaker has already tagged this node")
            return True
        return False

    def find_duplicates(self, attributes: list[AttributeAttribute]) -> list[NodeNode]:
        """
        Deteremine if there are matching objects in OMSB

        :param attributes: List of attributes to match nodes against in OMSB
        :return: List of duplicate nodes
        """

        node_attribute_subqueries: list[NodeAttributeSubQuery] = [
            NodeAttributeSubQuery(
                attributeIris=[attribute.attributeIri],
                attributeValue=StringQuery(equals=attribute.attributeValue, ignoreCase=True),
            )
            for attribute in attributes
        ]

        node_attribute_query: NodeAttributeQuery = NodeAttributeQuery(hasMatch=node_attribute_subqueries[0])
        if len(node_attribute_subqueries) > 1:
            node_attribute_query.and_ = [
                NodeAttributeQuery(hasMatch=subquery) for subquery in node_attribute_subqueries[1:]
            ]

        query: NodeQuery = NodeQuery(attributes=node_attribute_query)

        nodes_response = self.oms_crud_tool.get_nodes(query)

        if nodes_response and nodes_response.data:
            return nodes_response.data
        return []
