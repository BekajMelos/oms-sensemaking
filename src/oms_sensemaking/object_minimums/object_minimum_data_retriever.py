import logging

from oms_sdk.generated.generated_graphql_client import (
    AttributeQuery,
    NodeNode,
    RelationshipNodeQuery,
    RelationshipQuery,
)

from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER = logging.getLogger(__name__)


class ObjectMinimumDataRetriever:
    def retrieve_data_for_grading(
        self,
        oms_crud_tool: OmsCrudTool,
        node: NodeNode,
        required_attributes: list[str],
        required_relationships: list[str],
    ):
        iris_to_grade = {"attributes": None, "relationships": None}
        if required_attributes:
            try:
                attributes_to_grade = oms_crud_tool.get_attributes(
                    AttributeQuery(nodeIds=[node.id], attributeIris=required_attributes)
                )
                iris_to_grade["attributes"] = attributes_to_grade
            except Exception as e:
                LOGGER.error("Error retrieving attributes for node ID %s: %s", node.id, str(e))
                raise

        if required_relationships:
            try:
                relationships_to_grade = oms_crud_tool.get_relationships(
                    RelationshipQuery(
                        nodes=RelationshipNodeQuery(nodeIds=[node.id]), objectPropertyIris=required_relationships
                    )
                )
                iris_to_grade["relationships"] = relationships_to_grade
            except Exception as e:
                LOGGER.error("Error retrieving relationships for node ID %s: %s", node.id, str(e))
                raise

        return iris_to_grade
