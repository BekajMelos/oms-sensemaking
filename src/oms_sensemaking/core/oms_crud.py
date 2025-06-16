from typing import List, Optional, Union
from uuid import UUID

from oms_sdk import DEFAULT_ACM, get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivities,
    ActivityActivity,
    ActivityQuery,
    AttributeAttribute,
    AttributeQuery,
    AttributesAttributes,
    Client,
    CreateActivityCreateActivity,
    CreateActivityInput,
    CreateAttributeCreateAttribute,
    CreateAttributeInput,
    CreateNodeCreateNode,
    CreateNodeInput,
    CreateObservationCreateObservation,
    CreateObservationInput,
    CreateOriginatorCreateOriginator,
    CreateOriginatorInput,
    CreateProviderCreateProvider,
    CreateProviderInput,
    CreateRelationshipCreateRelationship,
    CreateRelationshipInput,
    CreateSourceCreateSource,
    CreateSourceInput,
    DeleteByIdInput,
    IdQuery,
    IriQuery,
    NodeNode,
    NodeQuery,
    NodesNodes,
    ObjectType,
    ObservationObservation,
    ObservationQuery,
    ObservationsObservations,
    OntologyClassOntologyClass,
    OriginatorQuery,
    OriginatorsOriginators,
    ProviderQuery,
    ProvidersProviders,
    RelationshipQuery,
    RelationshipsRelationships,
    SourceQuery,
    SourceSource,
    SourcesSources,
    StringQuery,
    UpdateActivityInput,
    UpdateActivityUpdateActivity,
    UpdateAttributeInput,
    UpdateAttributeUpdateAttribute,
    UpdateNodeInput,
    UpdateNodeUpdateNode,
    UpdateRelationshipInput,
    UpdateRelationshipUpdateRelationship,
    UpdateSourceInput,
    UpdateSourceUpdateSource,
)
from ratelimit import limits

from oms_sensemaking.config import SETTINGS


class OmsCrudTool:
    """Tool for using OMS_SDK CRUD operations"""

    def __init__(self) -> None:
        self.oms_client: Client = get_generated_graphql_client(
            url=SETTINGS.omsb_url,
            user_dn=SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
        )

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def publish_nodes(self, nodes: list[CreateNodeInput]) -> list[CreateNodeCreateNode]:
        """
        Publish the Nodes to OMS
        :param nodes: a list of CreateNodeInput objects
        """
        # 1. for each node, publish it to OMS
        return [self.oms_client.create_node(node) for node in nodes]

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def publish_relationships(
        self, relationships: list[CreateRelationshipInput]
    ) -> list[CreateRelationshipCreateRelationship]:
        """
        Publish the relationships to OMS
        :param relationships: a list of CreateRelationshipInput objects
        """
        # 1. for each relationship, publish it to OMS
        return [self.oms_client.create_relationship(relationship) for relationship in relationships]

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def publish_attributes(self, attributes: list[CreateAttributeInput]) -> list[CreateAttributeCreateAttribute]:
        """
        Publish the attributes to oms
        :param attributes: a list of CreateAttributeInput objects
        """
        # 1. for each attribute, publish it to OMS
        return [self.oms_client.create_attribute(attribute) for attribute in attributes]

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_node(self, node_input: CreateNodeInput) -> CreateNodeCreateNode:
        """
        Publish the Nodes to OMS
        :param node_input: a  CreateNodeInput object
        """
        # 1. for each node, publish it to OMS
        return self.oms_client.create_node(node_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_observation(self, observation_input: CreateObservationInput) -> CreateObservationCreateObservation:
        """
        Publish the Observations to OMS
        """
        return self.oms_client.create_observation(observation_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_relationship(self, relationship_input: CreateRelationshipInput) -> CreateRelationshipCreateRelationship:
        """
        Publish the relationship to OMS
        :param relationship_input: a CreateRelationshipInput object
        """
        # 1. for each relationship, publish it to OMS
        return self.oms_client.create_relationship(relationship_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_attribute(self, attribute_input: CreateAttributeInput) -> CreateAttributeCreateAttribute:
        """
        Publish the attribute to oms
        :param attribute_input: a CreateAttributeInput object
        """
        # 1. for each attribute, publish it to OMS
        return self.oms_client.create_attribute(attribute_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_activity(self, activity_input: CreateActivityInput) -> CreateActivityCreateActivity:
        """
        Publish the activity to oms
        :param activity_input: a CreateActivityInput object
        """
        # 1. for each activity, publish it to OMS
        return self.oms_client.create_activity(activity_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_source(self, source_input: CreateSourceInput) -> CreateSourceCreateSource:
        """
        Create a source in OMS
        :param source_input: a CreateSourceInput object
        """
        return self.oms_client.create_source(source_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_provider(self, provider_input: CreateProviderInput) -> CreateProviderCreateProvider:
        """
        Create a provider in OMS
        :param provider_input: a CreateProviderInput object
        """
        return self.oms_client.create_provider(provider_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_originator(self, originator_input: CreateOriginatorInput) -> CreateOriginatorCreateOriginator:
        """
        Create an Originator in OMS
        :param originator_input: a CreateOriginatorInput object
        """
        return self.oms_client.create_originator(originator_input)

    ### GET ###
    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_activity(self, id: UUID) -> ActivityActivity:
        """Get existing Activity from OMS"""
        activity = self.oms_client.activity(IdQuery(id=id))
        return activity

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_attribute(self, id: UUID) -> AttributeAttribute:
        """Get existing Attribute from OMS"""
        attribute = self.oms_client.attribute(IdQuery(id=id))
        return attribute

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_node(self, id: UUID) -> NodeNode:
        """Get existing Node from OMS"""
        node = self.oms_client.node(IdQuery(id=id))
        return node

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_observation(self, id: UUID) -> ObservationObservation:
        """Get existing Observation from OMS"""
        observation = self.oms_client.observation(IdQuery(id=id))
        return observation

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_nodes(self, node_info: NodeQuery) -> NodesNodes:
        """Get existing Node from OMS"""
        nodes = self.oms_client.nodes(query=node_info)
        return nodes

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_relationships(self, relationship_info: RelationshipQuery) -> RelationshipsRelationships:
        """Get existing Relationships from OMS"""
        relationships = self.oms_client.relationships(query=relationship_info)
        return relationships

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_attributes(self, attribute_info: AttributeQuery) -> AttributesAttributes:
        """Get existing Attributes from OMS"""
        attributes = self.oms_client.attributes(query=attribute_info)
        return attributes

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_activities(self, activity_info: ActivityQuery) -> ActivitiesActivities:
        """Get existing Activities from OMS"""
        activities = self.oms_client.activities(query=activity_info)
        return activities

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_observations(self, observation_info: ObservationQuery) -> ObservationsObservations:
        """Get existing Observations from OMS"""
        observations = self.oms_client.observations(query=observation_info)
        return observations

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_source(self, source_id: str) -> SourceSource:
        """Get existing Attributes from OMS"""
        source = self.oms_client.source(query=IdQuery(id=source_id))
        return source

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_source_by_name(self, source_name: str) -> SourcesSources:
        return self.oms_client.sources(query=SourceQuery(name=StringQuery(equals=source_name)))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_provider_by_name(self, provider_name: str) -> ProvidersProviders:
        """Get existing Attributes from OMS"""
        return self.oms_client.providers(query=ProviderQuery(name=StringQuery(equals=provider_name)))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_originator_by_name(self, originator_name: str) -> OriginatorsOriginators:
        """Get existing Attributes from OMS"""
        return self.oms_client.originators(query=OriginatorQuery(name=StringQuery(equals=originator_name)))

    ### UPDATE ###
    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def update_node(self, update_input: UpdateNodeInput) -> UpdateNodeUpdateNode:
        """Update node"""
        return self.oms_client.update_node(update_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def update_relationship(self, update_input: UpdateRelationshipInput) -> UpdateRelationshipUpdateRelationship:
        """Update relationship"""
        return self.oms_client.update_relationship(update_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def update_attribute(self, update_input: UpdateAttributeInput) -> UpdateAttributeUpdateAttribute:
        """Update attribute"""
        return self.oms_client.update_attribute(update_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def update_source(self, update_input: UpdateSourceInput) -> UpdateSourceUpdateSource:
        """Update source"""
        return self.oms_client.update_source(update_input)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def update_activity(self, update_input: UpdateActivityInput) -> UpdateActivityUpdateActivity:
        """Update activity"""
        return self.oms_client.update_activity(update_input)

    ### DELETE ###
    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def delete_node(self, node_id: str) -> bool:
        """Update node"""
        return self.oms_client.delete_node(DeleteByIdInput(id=node_id))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def delete_relationship(self, relationship_id: str) -> bool:
        """Update relationship"""
        return self.oms_client.delete_relationship(DeleteByIdInput(id=relationship_id))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def delete_attribute(self, attribute_id: str) -> bool:
        """Update attribute"""
        return self.oms_client.delete_attribute(DeleteByIdInput(id=attribute_id))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def delete_provider(self, provider_id: str) -> bool:
        return self.oms_client.delete_provider(DeleteByIdInput(id=provider_id))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def delete_originator(self, originator_id: str) -> bool:
        return self.oms_client.delete_originator(DeleteByIdInput(id=originator_id))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def delete_source(self, source_id) -> bool:
        return self.oms_client.delete_source(DeleteByIdInput(id=source_id))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_node_attribute_by_iri(self, node_id: UUID, iris: List[str]) -> List[AttributeAttribute]:
        """
        Given a node id and a list of IRIs, get the attribute values from OMS

        :param node_id: Node id to get attributes for
        :param iris: List of IRIs to get values for on the node
        :return: List of matching Attribute objects
        """
        query: AttributeQuery = AttributeQuery(attributeIris=iris, nodeIds=[node_id])
        attributes_response = self.get_attributes(query)
        if attributes_response and attributes_response.data:
            return attributes_response.data
        return []

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def rehydrate_oms_obj(
        self, object_id: UUID, object_type: ObjectType
    ) -> Union[ActivityActivity, AttributeAttribute, ObservationObservation, NodeNode]:
        """Get full OMS Object from id

        :param object_id: Id of OMS object to retrieve
        :param object_type: ObjectType type of object to retrieve
        """
        obj_getter_mapping = {
            ObjectType.ACTIVITY: self.get_activity,
            ObjectType.ATTRIBUTE: self.get_attribute,
            ObjectType.OBSERVATION: self.get_observation,
            ObjectType.NODE: self.get_node,
        }

        return obj_getter_mapping[object_type](object_id)

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        """Get the Ontology Class for a given iri

        :param iri: Iri to get ontology data for
        :return: Optional OntologyClass object
        """
        return self.oms_client.ontology_class(query=IriQuery(iri=iri))

    @limits(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period)
    def create_test_source(
        self,
        test_originator_name: str = "nlp_test_originator",
        test_provider_name: str = "nlp_test_provider",
        test_source_name: str = "nlp_test_source",
    ) -> CreateSourceCreateSource:
        """Creates an originator, a provider, and a source for test purposes"""
        # Create test originator if it doesn't already exist
        originator_by_name = self.get_originator_by_name(test_originator_name)
        if len(originator_by_name.data) > 0:
            originator = originator_by_name.data[0]
        else:
            originator = self.create_originator(
                CreateOriginatorInput(
                    name=test_originator_name,
                    description="A test originator",
                    acm=DEFAULT_ACM,
                    tags=SETTINGS.nlp_tags,
                )
            )

        # Create test provider if it doesn't already exist
        provider_by_name = self.get_provider_by_name(test_provider_name)
        if len(provider_by_name.data) > 0:
            provider = provider_by_name.data[0]
        else:
            provider = self.create_provider(
                CreateProviderInput(
                    name=test_provider_name,
                    description="A test provider",
                    originatorId=originator.id,
                    tags=SETTINGS.nlp_tags,
                    acm=DEFAULT_ACM,
                )
            )

        # Create test source if it doesn't already exist
        source_by_name = self.get_source_by_name(test_source_name)
        if len(source_by_name.data) > 0:
            source = source_by_name.data[0]
        else:
            source = self.create_source(
                CreateSourceInput(
                    name=test_source_name,
                    dateOfReport="2004-05-23T00:00:00-04:00",
                    dateOfInformation="2004-05-23T00:00:00-04:00",
                    tags=SETTINGS.nlp_tags,
                    providerId=provider.id,
                    acm=DEFAULT_ACM,
                    identifier="nlp_test_identifier",
                    dataAcm=DEFAULT_ACM,
                )
            )

        return source
