from geopy.distance import geodesic
from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
)
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    CreateAttributeInput,
    NodeQuery,
    NodeRelationshipQuery,
    NodeRelationshipSubQuery,
    StringQuery,
)

from oms_sensemaking.clients import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext


class AddOutOfGarrisonAttribute(BaseRule):
    """
    Detect when a node has a geolocation attribute,
    when a node has a geolocation attribute, compare it to garrison and add/update a new OutOfGarrison attribute
    pointing to the node
    """

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, input: RuleContext) -> bool:
        """
        Determine if the Attribute has a geo
        """
        return (
            input.attribute.geo
            and input.attribute.attributeIri == SETTINGS.inference_add_garrison_attribute_iri
        )

    def action(self, input: RuleContext):
        """
        Create an attribute that indicates if a node is garrisoned at a base or not
        """
        attr = input.attribute
        # Extracts the initial attribute coordinates
        base_attribute_geolocation = attr.geo

        # Runs a query to get the affiliated node
        node_response = oms_client.get_nodes(NodeQuery(
            ids=[attr.nodeId]
        ))
        dynamic_node = attr.nodeId

        # Check if the node is an Observational Node
        if(node_response.tier == "OBSERVATIONAL"):
            node_relationship_observational_response = oms_client.get_relationships(NodeRelationshipQuery(
                hasMatch=NodeRelationshipSubQuery(
                    objectPropertyIris=[SETTINGS.inference_participated_in_iri],
                    relatedNodeIds=[attr.nodeId]
                )
            ))
            # Gets the nodes that are related nodes from the Relationship Query
            for observational_relationship in node_relationship_observational_response:
                filtered_node_ids = [
                     node_id for node_id in observational_relationship.relatedNodeIds if node_id != attr.nodeId
                     ]
                dynamic_node = filtered_node_ids[0]

        # Runs a query on the PD (Primary/Derivative) Node
        node_relationship_pd_response = oms_client.get_relationships(NodeRelationshipQuery(
            hasMatch=NodeRelationshipSubQuery(
                objectPropertyIris=[SETTINGS.inference_garrison_location_iri],
                relatedNodeIds=[dynamic_node],
            )
        ))
        # Gets the nodes that are related nodes from the Relationship Query
        for pd_relationship in node_relationship_pd_response:
            filtered_node_ids = [
                node_id for node_id in pd_relationship.relatedNodeIds if node_id != dynamic_node
                ]
            garrison_node = filtered_node_ids[0]

        # Runs an Attribute Query to get the related Attribute
        final_attribute_response = oms_client.get_attributes(AttributeQuery(
            attributeIris=[SETTINGS.inference_garrison_location_iri],
            nodeId=garrison_node
        ))

        # Extracts the new attribute coordinates
        new_attribute_geolocation = final_attribute_response.geo
        geo_coordinates_1 = base_attribute_geolocation["features"][0]["geometry"]["coordinates"]
        geo_coordinates_2 = new_attribute_geolocation["features"][0]["geometry"]["coordinates"]

        # Library to calculate distances between coordinates in kilometers
        distance = geodesic(geo_coordinates_1, geo_coordinates_2).kilometers

        # Checks if the distance between coordinates is smaller than the requested distance 
        final_attribute_value = "Yes" if distance < SETTINGS.garrison_distance_kilometers else "No"

        # Creates a new attribute with the correct Attribute Value 
        attribute_out_of_garrison = CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_in_garrison_iri,
            attributeValue=final_attribute_value,
            attributeType=AttributeType.STRING,
            confidence=attr.confidence,
            sourceId=attr.sourceId,
            acm=attr.acm,
            isMutable=False,
            tags=SETTINGS.inference_tags
        )
        oms_client.create_attribute(attribute_out_of_garrison)

    def has_action_already_ran(self, input: RuleContext):
        """
        Determine if a metadata attribute has already been created for a node
        """

        attr = input.attribute
        if not attr:
            return False

        attribute_query = AttributeQuery(
            attributeIri=SETTINGS.inference_add_in_garrison_iri,
            attributeValue=StringQuery(equals="Yes"), # Yes or No, will check if this works
            attributeType={
                "is": AttributeType.STRING,
            },
            confidence={"is": (attr.confidence)},
            sourceId=attr.sourceId,
            nodeIds=[attr.nodeId],
            tags=SETTINGS.inference_tags,
        )

        res = oms_client.get_attributes(attribute_query)

        return len(res.data) > 0
