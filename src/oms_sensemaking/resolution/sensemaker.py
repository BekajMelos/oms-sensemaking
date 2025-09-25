"""Resolution Sensemakers."""

import logging
from dataclasses import dataclass, field
from itertools import chain
from typing import Tuple
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
from oms_sensemaking.resolution.attribute_combinations import AttributeCombinations

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

    def __init__(self, duplicate_object_iris: dict[str, list[str]], oms_crud_tool: OmsCrudTool) -> None:
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
        # can we print value
        LOGGER.debug(f"id: {attribute.id} attrIri: {attribute.attributeIri}")

        results = []

        criterion: list[list[AttributeAttribute]] = self.gather_criteria(attribute)
        if criterion:
            dups: list[NodeNode] = self.find_duplicates(criterion)
            dup_findings: list[DupFinding] = self.create_duplicate_findings(attribute, dups)
            results.extend(dup_findings)

        return results

    def gather_criteria(self, attribute: AttributeAttribute) -> list[list[AttributeAttribute]]:
        """
        Gather the criteria needed to check for duplicates in OMSB.

        :param attribute: Initial OMSB Attribute Object
        :return: List of possible lists of attributes to look for

        """
        valid, node_iri = self.is_valid(attribute)
        if not valid or node_iri is None:
            return []
        return AttributeCombinations(attribute, self.oms_crud_tool, self.duplicate_object_iris).gather(node_iri)

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

    def current_class_iri(self, attribute: AttributeAttribute) -> str:
        """
        A helper method that returns the current class IRI of the node associated with
        the current attribute being examined

        :param attribute: The current attribute associated with a node.
        :return: str value of the class IRI of the node
        """
        node_id = attribute.nodeId
        node = self.oms_crud_tool.get_node(node_id)
        return node.classIri

    def is_valid(self, current_attr: AttributeAttribute) -> Tuple[bool, str | None]:
        """
        A helper method that checks if the current attribute and the node
        it is associated with are valid objects that
        can be used to search for duplicate nodes

        :param current_attr: The current attribute which is associated with a node
        :return: bool value of whether the attribute and its node are valid
        """
        current_node_id = current_attr.nodeId
        if not current_node_id:
            return (False, None)

        current_iri = current_attr.attributeIri
        all_iris = set(chain.from_iterable(self.duplicate_object_iris.values()))
        if current_iri not in all_iris:
            return (False, None)

        if current_attr.attributeValue == "":
            return (False, None)

        class_iri = self.current_class_iri(current_attr)
        if class_iri not in self.duplicate_object_iris:
            return (False, None)

        if current_iri not in self.duplicate_object_iris[class_iri]:
            return (False, None)

        if self.has_already_ran(current_node_id):
            return (False, None)

        return (True, class_iri)

    def find_duplicates(self, combinations: list[list[AttributeAttribute]]) -> list[NodeNode]:
        """
        Determine if there are matching objects in OMSB

        :param combinations: A list of lists. The inner lists are various groupings and combinations
        of attributes coming from a current node that may match to other nodes' set of attributes
        :return: List of duplicate nodes
        """
        for group in combinations:
            node_attribute_subqueries: list[NodeAttributeSubQuery] = [
                NodeAttributeSubQuery(
                    attributeIris=[attribute.attributeIri],
                    attributeValue=StringQuery(equals=attribute.attributeValue, ignoreCase=True),
                )
                for attribute in group
            ]

            node_attribute_query: NodeAttributeQuery = NodeAttributeQuery(
                and_=[NodeAttributeQuery(hasMatch=subquery) for subquery in node_attribute_subqueries]
            )

            query: NodeQuery = NodeQuery(attributes=node_attribute_query)

            nodes_response = self.oms_crud_tool.get_nodes(query)

            if nodes_response and nodes_response.data:
                return nodes_response.data
        return []
