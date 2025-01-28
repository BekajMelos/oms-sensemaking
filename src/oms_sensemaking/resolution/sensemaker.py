"""Resolution Sensemakers."""

import copy
import logging
from dataclasses import dataclass, field
from typing import Dict, List
from uuid import UUID

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
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
    acm: Dict

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def get_acm(self) -> Dict:
        return self.acm


class DuplicateFacility:
    """Class to help find duplicate facilities in OMSB"""

    def __init__(self, oms_crud_tool: OmsCrudTool):

        self.oms_crud_tool = oms_crud_tool

        self.duplicate_facility_iris = SETTINGS.duplicate_facility_iris

    def meets_criteria(self, attribute: AttributeAttribute) -> List[AttributeAttribute]:
        """
        Gather the criteria needed to check for duplicates in OMSB.

        :param attribute: Initial OMSB Attribute Object
        :return: List of OMSB Attributes to look for

        """
        current_iri = attribute.attributeIri
        current_node_id = attribute.nodeId
        duplicate_facility_attributes = [attribute]

        if attribute.attributeIri not in self.duplicate_facility_iris or self.has_already_ran(current_node_id):
            return []

        # Get this nodes info and make sure we satisfy the requirements
        other_iris: List[str] = copy.copy(self.duplicate_facility_iris)
        other_iris.remove(current_iri)
        duplicate_facility_attributes.extend(self.get_node_attribute_by_iri(attribute.nodeId, other_iris))

        if len(duplicate_facility_attributes) != len(self.duplicate_facility_iris):
            LOGGER.debug("Node does not have all required fields for Duplicate Facility Matching. Ignoring.")
            return []

        return duplicate_facility_attributes

    def create_duplicate_findings(self, attribute: AttributeAttribute, nodes: List[NodeNode]) -> List[DupFinding]:
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

            dup = DupFinding(
                start_node_id=current_node_id,
                end_node_id=node.id,
                acm=node.acm
            )
            dups.append(dup)

            rel: CreateRelationshipInput = CreateRelationshipInput(
                name=SETTINGS.resolution_relationship_name,
                tags=[SETTINGS.resolution_sensemaker_tag],
                startNodeId=current_node_id,
                endNodeId=node.id,
                confidence=Confidence.HIGH.value,
                sourceId=attribute.sourceId,
                acm=attribute.acm,
                objectPropertyIri=SETTINGS.resolution_relationship_iri
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
            name=StringQuery(
                    equals=SETTINGS.resolution_relationship_name,
                    ignoreCase=True
                ),
            nodes=RelationshipNodeQuery(
                startNodeIds=[current_node_id]
            )
        )

        existing_relationships = self.oms_crud_tool.get_relationships(query)
        if existing_relationships and len(existing_relationships.data) > 0:
            LOGGER.debug("Sensemaker has already tagged this node")
            return True
        return False


    def get_node_attribute_by_iri(self, node_id: UUID, iris: List[str]) -> List[AttributeAttribute]:
        """
        Given a node id and a list of IRIs, get the attribute values from OMS

        :param node_id: Node id to get attributes for
        :param iris: List of IRIs to get values for on the node
        :return: List of matching Attribute objects
        """
        query: AttributeQuery = AttributeQuery(
            attributeIris=iris,
            nodeIds=[node_id]
        )
        attributes_response = self.oms_crud_tool.get_attributes(query)
        if attributes_response and attributes_response.data:
            return attributes_response.data
        return []


    def find_duplicates(self, attributes: List[AttributeAttribute]) -> List[NodeNode]:
        """
        Deteremine if there are matching objects in OMSB

        :param attributes: List of attributes to match nodes against in OMSB
        :return: List of duplicate nodes
        """

        node_attribute_subqueries: List[NodeAttributeSubQuery] = [
            NodeAttributeSubQuery(
                attributeIris=[attribute.attributeIri],
                attributeValue=StringQuery(
                    equals=attribute.attributeValue,
                    ignoreCase=True
                )
            ) for attribute in attributes]

        node_attribute_query: NodeAttributeQuery = NodeAttributeQuery(
            hasMatch=node_attribute_subqueries[0]
        )
        if len(node_attribute_subqueries) > 1:
            node_attribute_query.and_ = [
                NodeAttributeQuery(
                    hasMatch=subquery
                )
            for subquery in node_attribute_subqueries[1:]]

        query: NodeQuery = NodeQuery(
            attributes=node_attribute_query
        )

        nodes_response = self.oms_crud_tool.get_nodes(query)

        if nodes_response and nodes_response.data:
            return nodes_response.data
        return []


class ResolutionSensemaker(Sensemaker):
    """
    A sensemaker for detecting duplicate nodes in omsb.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "resolution" algorithm implementation.

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of ResolutionSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}
        self.oms_crud_tool = oms_crud_tool

        # Register duplicate data checks
        self.duplicate_checks = [
            DuplicateFacility(self.oms_crud_tool)
        ]

    def process_data(self, attribute: AttributeAttribute) -> List[DupFinding]:
        """
        Determine if a created Node is the same as an existing note and suggest that they are merged

        :param attribute: The attribute to analyze.
        :return: List[DupFinding] List of duplicates found
        """
        LOGGER.info("Running Resolution Sensemaker")
        LOGGER.debug(f"{attribute.attributeIri}: {attribute.attributeValue}")

        results = []

        for dup in self.duplicate_checks:
            criterion: List[AttributeAttribute] = dup.meets_criteria(attribute)
            if criterion:

                dups: List[NodeNode] = dup.find_duplicates(criterion)

                dup_findings: List[DupFinding] = dup.create_duplicate_findings(attribute, dups)
                results.extend(dup_findings)

        return results
