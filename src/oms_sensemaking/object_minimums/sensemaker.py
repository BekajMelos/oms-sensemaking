"""Object Minimums Sensemakers."""

import logging

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
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

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of ResolutionSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}
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
        sample_config = {
            "https://oms.dodiis.ic.gov/ontology/c-0000000002": {
                "ATTRIBUTES": [
                    "https://oms.dodiis.ic.gov/ontology/p-0000000002",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000001",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000006",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000003",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000004",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000005",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000008",
                    "https://oms.dodiis.ic.gov/ontology/p-0000000022",
                ],
                "RELATIONSHIPS": [],
            }
        }
        class_iri = self.oms_crud_tool.get_node(attribute_of_node.nodeId).classIri
        reqs_attr_iris = sample_config[class_iri].get("ATTRIBUTES")
        reqs_rel_iris = sample_config[class_iri].get("RELATIONSHIPS")
        required_iris = reqs_attr_iris + reqs_rel_iris
        rubric = ObjectMinimumRubric(required_iris=required_iris)
        grade = rubric.grade(
            attributes=[
                "https://oms.dodiis.ic.gov/ontology/p-0000000002",
                "https://oms.dodiis.ic.gov/ontology/p-0000000001",
            ],
            relationships=[],
        )
        LOGGER.info("Object Minimum grade: %s", grade.completion_score)

        return []
