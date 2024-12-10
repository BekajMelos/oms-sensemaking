
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
        Determine if the Attribute is a geo attribute for a node
        """

        return (
            input.attribute
            and input.attribute.attributeIri == SETTINGS.inference_add_garrison_attribute_iri
            and input.attribute.attributeValue
        )

    def action(self, input: RuleContext):
        """
        Create an attribute that indicates if a node is garrisoned at a base or not
        """
        attr = input.attribute

        try:
            if attr.geo is None:
                raise AttributeError("The attribute does not have a geo")
        except AttributeError as e:
            # Need some clarification on how we want to handle scenarios where attributes don't have geos
            print(f"Error: {e}")

        base_attribute_geolocation = attr.geo

        node_response = oms_client.get_nodes(NodeQuery(
            ids=[attr.nodeId]
        ))
        tank_node = attr.nodeId

        if(node_response.tier == "OBSERVATIONAL"):
            node_relationship_observational_response = oms_client.get_relationships(NodeRelationshipQuery(
                hasMatch=NodeRelationshipSubQuery(
                    objectPropertyIris=[SETTINGS.inference_participated_in_iri],
                    relatedNodeIds=[attr.nodeId]
                )
            ))

            for observational_relationship in node_relationship_observational_response:
                filtered_node_ids = [
                     node_id for node_id in observational_relationship.relatedNodeIds if node_id != attr.nodeId
                     ]
                tank_node = filtered_node_ids[0]

        # PD Query stands for Primary/Derivative
        node_relationship_pd_response = oms_client.get_relationships(NodeRelationshipQuery(
            hasMatch=NodeRelationshipSubQuery(
                objectPropertyIris=[SETTINGS.inference_garrison_location_iri],
                relatedNodeIds=[tank_node],
            )
        ))
        for pd_relationship in node_relationship_pd_response:
            filtered_node_ids = [
                node_id for node_id in pd_relationship.relatedNodeIds if node_id != tank_node
                ]
            garrison_node = filtered_node_ids[0]

        final_attribute_response = oms_client.get_attributes(AttributeQuery(
            attributeIris=[SETTINGS.inference_garrison_location_iri],
            nodeId=garrison_node
        ))

        new_attribute_geolocation = final_attribute_response.geo
        geo_coordinates_1 = base_attribute_geolocation["features"][0]["geometry"]["coordinates"]
        geo_coordinates_2 = new_attribute_geolocation["features"][0]["geometry"]["coordinates"]

        # Library to calculate distances between coordinates in kilometers
        distance = geodesic(geo_coordinates_1, geo_coordinates_2).kilometers

        final_attribute_value = "Yes" if distance < SETTINGS.garrison_distance_kilometers else "No"

        attribute_out_of_garrison = CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_is_garrison_at_iri,
            attributeValue=final_attribute_value,
            attributeType=AttributeType.STRING,
            confidence=attr.confidence,
            sourceId=attr.sourceId,
            acm=attr.acm,
            isMutable=False
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
            attributeIri=SETTINGS.inference_add_garrison_attribute_meta_data_iri,
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
