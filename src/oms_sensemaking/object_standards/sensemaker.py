"""Object Standards Sensemakers."""

import logging
from datetime import datetime, timezone

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    CreateObjectStandardsInput,
    NodeNode,
    NodeQuery,
    ObjectStandardsObjectStandardsData,
    ObjectStandardsQuery,
    RelationshipRelationship,
    UpdateObjectStandardsInput,
    UuidQueryByList,
)

from oms_sensemaking.clients.aac_client import HasAcm
from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.object_standards.object_standards_data_retriever import ObjectStandardsDataRetriever
from oms_sensemaking.object_standards.object_standards_models import (
    ObjectStandardsGrade,
    ObjectStandardsRubric,
    RequiredIris,
)

LOGGER = logging.getLogger(__name__)


class ObjectStandards(Sensemaker):
    """
    A sensemaker for grading object completeness.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial object standards sensemaker

    """

    def __init__(
        self,
        oms_crud_tool: OmsCrudTool,
        ontology_service: OntologyService,
        obj_standards_retriever: ObjectStandardsDataRetriever,
        obj_standards_rubric: ObjectStandardsRubric,
        rubric_criteria: dict,
    ) -> None:
        """Create a new instance of ObjectStandards sensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.rubric_criteria = rubric_criteria
        self.oms_crud_tool = oms_crud_tool
        self.ontology_service = ontology_service
        self.obj_standards_rubric = obj_standards_rubric
        self.obj_standards_retriever = obj_standards_retriever

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
            if isinstance(node_characteristic, AttributeAttribute):
                node_ids = [node_characteristic.nodeId]
            elif isinstance(node_characteristic, RelationshipRelationship):
                node_ids = [node_characteristic.startNodeId, node_characteristic.endNodeId]
            else:
                LOGGER.warning(
                    "Unexpected characteristic type %s in ObjectStandards",
                    type(node_characteristic),
                )
                return []
            node_query = NodeQuery(ids=node_ids)
            nodes = self.oms_crud_tool.get_nodes(node_query)
            for node in nodes.data:
                object_standard_query = ObjectStandardsQuery(
                    nodeIds=UuidQueryByList(in_=[node.id]),
                )
                existing_object_standards = self.oms_crud_tool.get_object_standards(object_standard_query).data
                required_iris = self._get_required_iris(node)

                # The case where there is nothing to grade.
                # Still valid if one exists, but the other does not (i.e. rel iris exist, but not attr iris)
                # Can still grade based off rels if thats all there is. *At least one needs to exist
                if not required_iris.attribute_iris and not required_iris.relationship_iris:
                    LOGGER.info(
                        "Ungradeable class object. Grade was not able to be calculated for the node with id: %s",
                        node.id,
                    )
                    continue
                else:
                    # set the required IRIs for the rubric
                    self.obj_standards_rubric.required_attrs = required_iris.attribute_iris
                    self.obj_standards_rubric.required_rels = required_iris.relationship_iris

                # retrieve the 'available' data connected to the node of interest
                retrieved_node_data = self.obj_standards_retriever.retrieve_data_for_grading(
                    self.oms_crud_tool, node, required_iris.attribute_iris, required_iris.relationship_iris
                )

                # Extract the actual attribute and relationship objects for grading
                node_attributes = retrieved_node_data["attributes"]
                node_relationships = retrieved_node_data["relationships"]

                grade = self.obj_standards_rubric.grade(node_attributes, node_relationships)
                classified_objects: list[HasAcm]
                if node_attributes and node_relationships:
                    classified_objects = [node] + node_attributes + node_relationships
                elif node_attributes and not node_relationships:
                    classified_objects = [node] + node_attributes
                elif node_relationships and not node_attributes:
                    classified_objects = [node] + node_relationships
                else:
                    classified_objects = [node]
                rolled_up_acm = aac_client.get_acm_rollup(
                    [{"ACM": classified_object.acm} for classified_object in classified_objects]
                )
                self.publish_results_to_atoms(node, existing_object_standards, rolled_up_acm, grade)
        except Exception as e:
            LOGGER.error("Error processing object standards data for object(s) %s: %s", node_ids, str(e))

        return []

    def generate_summary_string(self, float_score, ratio_score, violations_length, compliant_obj_length):
        summary = (
            f"This object has an object standards score of {float_score} ({ratio_score}). "
            f"This object has {violations_length} violations and {compliant_obj_length} compliant objects"
        )
        return summary

    def publish_results_to_atoms(
        self,
        node: NodeNode,
        existing: list[ObjectStandardsObjectStandardsData],
        rolled_up_acm: dict,
        grade: ObjectStandardsGrade,
    ):
        summary = self.generate_summary_string(
            grade.float_score, grade.ratio, len(grade.violations), len(grade.compliant_fields)
        )
        if existing:
            update_object_standards_input = UpdateObjectStandardsInput(
                id=existing[0].id,
                acm=rolled_up_acm,
                summary=summary,
                score=grade.float_score,
                violations=grade.violations,
                compliantObjects=grade.compliant_fields,
                timestamp=datetime.now(tz=timezone.utc),
                standardsVersion=self.version_string,
            )
            self.oms_crud_tool.update_object_standards(update_object_standards_input)
        else:
            object_standards_input = CreateObjectStandardsInput(
                acm=rolled_up_acm,
                tags=SETTINGS.object_standards_settings.tags,
                nodeId=node.id,
                summary=summary,
                score=grade.float_score,
                violations=grade.violations,
                compliantObjects=grade.compliant_fields,
                timestamp=datetime.now(tz=timezone.utc),
                standardsVersion=self.version_string,
            )
            self.oms_crud_tool.create_object_standards(object_standards_input)

    def _get_rubric_requirements(self, class_iri: str) -> RequiredIris | None:
        """Return RequiredIris if class has a rubric with at least one requirement."""
        config_rubric_data = self.rubric_criteria.get(class_iri, {})
        reqs_attr_iris = config_rubric_data.get("ATTRIBUTES", [])
        reqs_rel_iris = config_rubric_data.get("RELATIONSHIPS", [])
        if reqs_attr_iris or reqs_rel_iris:
            return RequiredIris(attribute_iris=reqs_attr_iris, relationship_iris=reqs_rel_iris)
        return None

    def _get_required_iris(self, node: NodeNode) -> RequiredIris:
        """
        Get required IRIs for a node's class by traversing up the class hierarchy.

        First checks the node's class_iri, then traverses up parent classes
        until a rubric is found or max_rubric_hierarchy_levels (config) have been checked.

        :param node: The node whose class IRI (and ancestor chain) to use
        :return: RequiredIris with attribute_iris and relationship_iris
        """
        class_iri = node.classIri
        reqs = self._get_rubric_requirements(class_iri)
        if reqs is not None:
            return reqs

        ancestor_iris = self.ontology_service.get_node_ancestors_iris(node)
        max_ancestors_to_check = SETTINGS.object_standards_settings.max_rubric_hierarchy_levels - 1
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
            SETTINGS.object_standards_settings.max_rubric_hierarchy_levels,
        )
        return RequiredIris()
