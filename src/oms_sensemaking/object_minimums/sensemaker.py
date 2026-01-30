"""Object Minimums Sensemakers."""

import logging

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributesAttributesData,
    NodeNode,
    NodeQuery,
    RelationshipRelationship,
    RelationshipsRelationshipsData,
)

from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.object_minimums.object_minimum_data_retriever import ObjectMinimumDataRetriever
from oms_sensemaking.object_minimums.object_minimum_models import ObjectMinimumRubric

LOGGER = logging.getLogger(__name__)


class ObjectMinimums(Sensemaker):
    """
    A sensemaker for grading object completeness.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial object minimums sensemaker

    """

    def __init__(
        self,
        oms_crud_tool: OmsCrudTool,
        ontology_service: OntologyService,
        obj_min_retriever: ObjectMinimumDataRetriever,
        obj_min_rubric: ObjectMinimumRubric,
        rubric_criteria: dict,
    ) -> None:
        """Create a new instance of ObjectMinimums sensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.rubric_criteria = rubric_criteria
        self.oms_crud_tool = oms_crud_tool
        self.ontology_service = ontology_service
        self.obj_min_rubric = obj_min_rubric
        self.obj_min_retriever = obj_min_retriever

    def process_data(
        self,
        node_characteristic: AttributeAttribute | RelationshipRelationship,
        config: dict | None = None,
    ):
        """
        Determine the completeness of an ATOMS node based off its various related components

        :param attribute_of_node: The objects attribute to analyze (will be expanding to
        other descriptive objects in the future)
        :return: Grade
        """
        try:
            # attribute has only one node it is associated with, relationships
            # have a start node and end node. hard to tell what exactly is the node
            # we care about, so let's just care for both

            """
            what I want to do here in the future is to check if it is attr and rel
            and call a custom class/function to retr data all at once with a custom query

            get node(s)
            get node(s) attrs and rels
            send the data through helper functions

            this will allow us to eliminate the .retrieve_data_for_grading()
            or instead move it up/modify it to grab all data all at once
            """
            if isinstance(node_characteristic, AttributeAttribute):
                node_ids = [node_characteristic.nodeId]
            elif isinstance(node_characteristic, RelationshipRelationship):
                node_ids = [node_characteristic.startNodeId, node_characteristic.endNodeId]
            else:
                LOGGER.warning(
                    "Unexpected characteristic type %s in ObjectMinimums",
                    type(node_characteristic),
                )
                return []
            node_query = NodeQuery(ids=node_ids)
            nodes = self.oms_crud_tool.get_nodes(node_query)
            for node in nodes.data:
                required_attr_iris, required_rel_iris = self._get_required_iris(node)

                # The case where there is nothing to grade.
                # Still valid if one exists, but the other does not (i.e. rel iris exist, but not attr iris)
                # Can still grade based off rels if thats all there is. *At least one needs to exist
                if not required_attr_iris and not required_rel_iris:
                    LOGGER.info(
                        "Ungradeable class object. Grade was not able to be calculated for the node with id: %s",
                        node.id,
                    )
                    continue
                else:
                    # set the required IRIs for the rubric
                    self.obj_min_rubric.required_attrs = required_attr_iris
                    self.obj_min_rubric.required_rels = required_rel_iris

                # retrieve the 'available' data connected to the node of interest
                retrieved_node_data = self.obj_min_retriever.retrieve_data_for_grading(
                    self.oms_crud_tool, node, required_attr_iris, required_rel_iris
                )
                grade = self._calculate_grade(retrieved_node_data["attributes"], retrieved_node_data["relationships"])
                # TODO: Update the node metadata with grade (amongst other various fields) once schema support exists
                LOGGER.info("Object Minimum float grade for object %s: %s", node.id, grade.float_score)
                LOGGER.info("Object Minimum ratio grade for object %s: %s", node.id, grade.ratio)
                LOGGER.info("Object Minimums violations for object %s: %s", node.id, grade.violations)
        except Exception as e:
            LOGGER.error("Error processing object minimum data for object(s) %s: %s", node_ids, str(e))

        return []

    def _get_rubric_requirements(self, class_iri: str) -> tuple[list[str], list[str]] | None:
        """Return (required_attrs, required_rels) if class has a rubric with at least one requirement."""
        config_rubric_data = self.rubric_criteria.get(class_iri, {})
        reqs_attr_iris = config_rubric_data.get("ATTRIBUTES", [])
        reqs_rel_iris = config_rubric_data.get("RELATIONSHIPS", [])
        if reqs_attr_iris or reqs_rel_iris:
            return (reqs_attr_iris, reqs_rel_iris)
        return None

    def _get_required_iris(self, node: NodeNode) -> tuple[list[str], list[str]]:
        """
        Get required IRIs for a node's class by traversing up the class hierarchy.

        First checks the node's class_iri, then traverses up parent classes
        until a rubric is found or max_rubric_hierarchy_levels (config) have been checked.

        :param node: The node whose class IRI (and ancestor chain) to use
        :return: Tuple of (required_attributes, required_relationships)
        """
        class_iri = node.classIri
        reqs = self._get_rubric_requirements(class_iri)
        if reqs is not None:
            return reqs

        ancestor_iris = self.ontology_service.mil_symbol_get_node_ancestors_iris(node)
        max_ancestors_to_check = SETTINGS.object_minimum_settings.max_rubric_hierarchy_levels - 1
        for ancestor_iri in ancestor_iris[:max_ancestors_to_check]:
            reqs = self._get_rubric_requirements(ancestor_iri)
            if reqs is not None:
                LOGGER.info(
                    "Found rubric for parent class %s when checking class %s",
                    ancestor_iri,
                    class_iri,
                )
                return reqs

        LOGGER.info(
            "No rubric found for class %s after checking %d levels in the hierarchy",
            class_iri,
            SETTINGS.object_minimum_settings.max_rubric_hierarchy_levels,
        )
        return [], []

    def _calculate_grade(
        self,
        attributes: list[AttributesAttributesData] | None,
        relationships: list[RelationshipsRelationshipsData] | None,
    ):
        try:
            return self.obj_min_rubric.grade(attributes=attributes, relationships=relationships)
        except Exception as e:
            LOGGER.error("Error calculating grade: %s", str(e))
            raise
