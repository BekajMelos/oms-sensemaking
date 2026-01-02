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

    def __init__(self, oms_crud_tool: OmsCrudTool, config: dict, rubrics: dict) -> None:
        """Create a new instance of ResolutionSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = config
        self.rubrics = rubrics
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
            # Retrieve node
            node = self.oms_crud_tool.get_node(attribute_of_node.nodeId)
            class_iri = node.classIri

            # Retrieve rubric requirements
            rubric_data = self.rubrics.get(class_iri, {})
            reqs_attr_iris = rubric_data.get("ATTRIBUTES", [])
            reqs_rel_iris = rubric_data.get("RELATIONSHIPS", [])
            required_iris = reqs_attr_iris + reqs_rel_iris

            if not required_iris:
                LOGGER.info("Object Minimum grade not calculated due to lack of required IRIs")
                return []

            # Initialize and use the rubric
            rubric = ObjectMinimumRubric(required_iris=required_iris)
            attributes_to_grade = self.oms_crud_tool.get_attributes(AttributeQuery(nodeIds=[node.id]))
            relationships_to_grade = self.oms_crud_tool.get_relationships(
                RelationshipQuery(nodes=RelationshipNodeQuery(nodeIds=[node.id]))
            )
            grade = rubric.grade(attributes=attributes_to_grade, relationships=relationships_to_grade)

            LOGGER.info("Object Minimum grade: %s", grade.completion_score)
            return []

        except Exception as e:
            LOGGER.error("Error processing data for node ID %s: %s", node.id, str(e))
            return []
