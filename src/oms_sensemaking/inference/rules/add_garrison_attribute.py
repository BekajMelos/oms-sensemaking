from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
)
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    NodeQuery,
    NodeRelationshipQuery,
    NodeRelationshipSubQuery,
    CreateAttributeInput,
    StringQuery,
)

from oms_sensemaking.clients import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext

class AddGarrisonAttribute(BaseRule):
    """
    Detect when a node has a Name attribute,
    when a node has a Name attribute, add a new HasName attribute
    pointing to the node

    Detect when a node has a geolocation attribute,
    when a node has a geolocation attribute, compare it to garrison and add/update a new OutOfGarrison attribute
    pointing to the node
    """

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, input: RuleContext) -> bool:
        """
        Determine if the Attribute is a Name attribute for a node

        Determine if the Attribute is a geo attribute for a node
        """

        print("**************** EVALUATE START ********************")

        return (
            input.attribute
            and input.attribute.attributeIri == SETTINGS.inference_add_garrison_attribute_iri
            and input.attribute.attributeValue
        )
    
        # Everything below won't run
        return (
            input.attribute
            and input.attribute.attributeIri == SETTINGS.inference_add_has_name_attribute_iri
            and input.attribute.attributeValue
        )

    def action(self, input: RuleContext):
        """
        Create a metadata attribute for a node that indicates that it has a name

        Create a metadata attribute for a node that indicates if it is out of garrisoned or not
        """

        print("************ACTION START**************")
        attr = input.attribute

        if attr.geo is None:
            # YOU CAN USE ATTR.HASGEO HERE
            print("NOT A GEO")

        base_attribute_geolocation = attr.geo

        print("attribute node ID = ", attr.nodeId)

        nodeResponse = oms_client.get_nodes(NodeQuery(
            ids=[attr.nodeId]
        ))

        print("Node id = ", nodeResponse.id)
        print("Node name = ", nodeResponse.name)
        print("Node tier = ", nodeResponse.tier)

        tankNode = attr.nodeId
        print("Tank Node = ", tankNode)

        if(nodeResponse.tier == "OBSERVATIONAL"):
            print("OBSERVATIONAL NODE")
            nodeRelationshipObservationalResponse = oms_client.get_relationships(NodeRelationshipQuery(
                hasMatch=NodeRelationshipSubQuery(
                    objectPropertyIris=[SETTINGS.inference_participated_in_iri],
                    relatedNodeIds=[attr.nodeId]
                )
            ))

            for observational_relationship in nodeRelationshipObservationalResponse: 
                print("RESPONSE NAME = ", observational_relationship.name)
                print("RELATED NODE ID'S = ", observational_relationship.relatedNodeIds)
                filtered_node_ids = [
                     node_id for node_id in observational_relationship.relatedNodeIds if node_id != attr.nodeId
                     ]
                print("FILTERED RELATED NODE IDS = ", filtered_node_ids)
                tankNode = filtered_node_ids[0]
                print(tankNode)
        
        # PD Query stands for Primary/Derivative
        print("PD RELATIONSHIP QUERY")
        nodeRelationshipPDResponse = oms_client.get_relationships(NodeRelationshipQuery(
            hasMatch=NodeRelationshipSubQuery(
                objectPropertyIris=[SETTINGS.inference_garrison_location_iri],
                relatedNodeIds=[tankNode],
            )
        ))
        for pd_relationship in nodeRelationshipPDResponse: 
            print("RESPONSE NAME = ", pd_relationship.name)
            print("RELATED NODE ID'S = ", pd_relationship.relatedNodeIds)
            filtered_node_ids = [
                node_id for node_id in pd_relationship.relatedNodeIds if node_id != tankNode
                ]
            garrisonNode = filtered_node_ids[0]
            print("Garrison Node = ", garrisonNode)


        # DONE WITH RELATIONSHIP QUERIES

        newAttributeQuery = AttributeQuery(
            attributeIris=SETTINGS.inference_garrison_location_iri,
            nodeIds=garrisonNode
        )
        print("NOW WE HAVE THE SECOND ATTRIBUTE", newAttributeQuery)

        new_attribute_geolocation = newAttributeQuery.geoQuery

        #Logic for geolocation distance, going to make it work later
        if(new_attribute_geolocation == base_attribute_geolocation):
            finalAttributeValue = "Yes"
        else:
            finalAttributeValue = "No"

        attribute = CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_is_garrison_at_iri,
            attributeValue=finalAttributeValue,
            attributeType=AttributeType.STRING,
            confidence=attr.confidence,
            sourceId=attr.sourceId,
            acm=attr.acm,
            isMutable="false"
        )

        """
        attr = input.attribute
        attribute = CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue="true",
            attributeType=AttributeType.BOOLEAN,
            confidence=attr.confidence,
            sourceId=attr.sourceId,
            nodeId=attr.nodeId,
            acm=attr.acm,
            tags=SETTINGS.inference_tags,
        )
        """

        oms_client.create_attribute(attribute)

    def has_action_already_ran(self, input: RuleContext):
        """
        Determine if a metadata attribute has already been created for a node
        """

        attr = input.attribute
        if not attr:
            return False

        attribute_query = AttributeQuery(
            attributeIri=SETTINGS.inference_add_garrison_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Yes" or "No"), #dunno if this works
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
        
        # Everything below won't run
        
        attr = input.attribute
        if not attr:
            return False

        attribute_query = AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="true"),
            attributeType={
                "is": AttributeType.BOOLEAN,
            },
            confidence={"is": (attr.confidence)},
            sourceId=attr.sourceId,
            nodeIds=[attr.nodeId],
            tags=SETTINGS.inference_tags,
        )

        res = oms_client.get_attributes(attribute_query)

        return len(res.data) > 0
