"""Object Minimums Sensemakers."""

import logging

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.object_minimums import ObjectMinimumRubric

LOGGER = logging.getLogger(__name__)


class ObjectMinimums(Sensemaker):
    """
    A sensemaker for grading object completeness.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial object minimums sensemaker

    """

    def __init__(self, oms_crud_tool: OmsCrudTool, config_settings: dict, config_rubrics: dict) -> None:
        """Create a new instance of ResolutionSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config_settings = config_settings
        self.config_rubrics = config_rubrics
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, attribute_of_node: AttributeAttribute, config: dict | None = None):
        """
        Determine the completeness of an ATOMS node based off its various related components

        :param attribute_of_node: The objects attribute to analyze (will be expanding to
        other descriptive objects in the future)
        :return: Grade
        """
        LOGGER.info("Running Object Minimums Sensemaker")

        """
        possible structure:

        Probably get the node object by doing: node = crud_tool.get_node(attribute_of_node.nodeId)

        Look at the node obj class iri: iri = node.iri

        call some sort of helper function(s) below to call the grading class

        run the grading rubric made for the specific class iri on the node

        retrieve the grade

        pass the grade to another helper to push the grade info to
        the node's metadata (discussed with effects team) is this an update? (unsure)
        """

        try:
            node = self._retrieve_node(attribute_of_node.nodeId)
            class_iri = node.classIri
            required_iris = self._get_required_iris(class_iri)

            if not required_iris:
                LOGGER.info("Object Minimum grade not calculated due to lack of required IRIs")
                return []

            attributes_to_grade, relationships_to_grade = self._retrieve_data_for_grading(node)
            grade = self._calculate_grade(attributes_to_grade, relationships_to_grade, required_iris)

            LOGGER.info("Object Minimum grade: %s", grade.completion_score)
        except Exception as e:
            LOGGER.error("Error processing object minimum data for node ID %s: %s", attribute_of_node.nodeId, str(e))

        return []

    def _retrieve_node(self, node_id):
        try:
            return self.oms_crud_tool.get_node(node_id)
        except Exception as e:
            LOGGER.error("Unexpected error retrieving node ID %s: %s", node_id, str(e))
            raise

    def _get_required_iris(self, class_iri):
        try:
            config_rubric_data = self.config_rubrics.get(class_iri, {})
            reqs_attr_iris = config_rubric_data.get("ATTRIBUTES", [])
            reqs_rel_iris = config_rubric_data.get("RELATIONSHIPS", [])
            return reqs_attr_iris + reqs_rel_iris
        except KeyError as e:
            LOGGER.error("Missing configuration for class IRI %s: %s", class_iri, str(e))
            raise
        except Exception as e:
            LOGGER.error("Unexpected error retrieving required IRIs for class IRI %s: %s", class_iri, str(e))
            raise

    def _retrieve_data_for_grading(self, node):
        try:
            attributes_to_grade = self.oms_crud_tool.get_attributes(AttributeQuery(nodeIds=[node.id]))
        except Exception as e:
            LOGGER.error("Error retrieving attributes for node ID %s: %s", node.id, str(e))
            raise

        try:
            relationships_to_grade = self.oms_crud_tool.get_relationships(
                RelationshipQuery(nodes=RelationshipNodeQuery(nodeIds=[node.id]))
            )
        except Exception as e:
            LOGGER.error("Error retrieving relationships for node ID %s: %s", node.id, str(e))
            raise

        return attributes_to_grade, relationships_to_grade

    def _calculate_grade(self, attributes, relationships, required_iris):
        try:
            rubric = ObjectMinimumRubric(required_iris=required_iris)
            return rubric.grade(attributes=attributes, relationships=relationships)
        except Exception as e:
            LOGGER.error("Error calculating grade: %s", str(e))
            raise
