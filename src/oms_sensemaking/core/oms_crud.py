import logging
import warnings
from typing import List, Optional, Union
from uuid import UUID

from cachetools import TTLCache, cached
from oms_sdk import get_generated_graphql_client
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
    PageParams,
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
    UuidQueryByList,
)

from oms_sensemaking.clients.base_client import BaseClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.rate_limiter import rate_limiter

LOGGER: logging.Logger = logging.getLogger(__name__)


@rate_limiter(calls=SETTINGS.maximum_oms_api_calls, period=SETTINGS.oms_api_call_period_seconds)
class OmsCrudTool(BaseClient):
    """Tool for using OMS_SDK CRUD operations"""

    def __init__(self, user_dn: str | None = None) -> None:
        super().__init__(host=SETTINGS.omsb_host, port=SETTINGS.omsb_port, service_name="OMS")

        self.oms_client: Client = get_generated_graphql_client(
            url=SETTINGS.omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
        )

    def _ensure_pagination_params(
        self, query_obj: Union[NodeQuery, RelationshipQuery, AttributeQuery, ActivityQuery, ObservationQuery]
    ) -> None:
        """Ensure pagination parameters are set on query objects if pagination is enforced."""
        if SETTINGS.enforce_graphql_pagination:
            page_params = getattr(query_obj, "pageParams", None)
            if not page_params:
                query_obj.pageParams = PageParams(page=1, pageSize=SETTINGS.graphql_default_page_size)
            else:
                # Ensure page is set (defaults to 1 if not provided)
                if not hasattr(query_obj.pageParams, "page") or query_obj.pageParams.page is None:
                    query_obj.pageParams.page = 1
                # Validate and limit pageSize to prevent data mining
                if not hasattr(query_obj.pageParams, "pageSize") or query_obj.pageParams.pageSize is None:
                    query_obj.pageParams.pageSize = SETTINGS.graphql_default_page_size
                elif query_obj.pageParams.pageSize > SETTINGS.graphql_default_page_size:
                    LOGGER.warning(
                        "Page size %d exceeds maximum allowed %d, limiting to default size",
                        query_obj.pageParams.pageSize,
                        SETTINGS.graphql_default_page_size,
                    )
                    query_obj.pageParams.pageSize = SETTINGS.graphql_default_page_size

    def publish_nodes(self, nodes: list[CreateNodeInput]) -> list[CreateNodeCreateNode]:
        """
        Publish the Nodes to OMS
        :param nodes: a list of CreateNodeInput objects
        """
        # 1. for each node, publish it to OMS
        return [self.oms_client.create_node(node) for node in nodes]

    def publish_relationships(
        self, relationships: list[CreateRelationshipInput]
    ) -> list[CreateRelationshipCreateRelationship]:
        """
        Publish the relationships to OMS
        :param relationships: a list of CreateRelationshipInput objects
        """
        # 1. for each relationship, publish it to OMS
        return [self.oms_client.create_relationship(relationship) for relationship in relationships]

    def publish_attributes(self, attributes: list[CreateAttributeInput]) -> list[CreateAttributeCreateAttribute]:
        """
        Publish the attributes to oms
        :param attributes: a list of CreateAttributeInput objects
        """
        # 1. for each attribute, publish it to OMS
        return [self.oms_client.create_attribute(attribute) for attribute in attributes]

    def create_node(self, node_input: CreateNodeInput) -> CreateNodeCreateNode:
        """
        Publish the Nodes to OMS
        :param node_input: a  CreateNodeInput object
        """
        # 1. for each node, publish it to OMS
        return self.oms_client.create_node(node_input)

    def create_observation(self, observation_input: CreateObservationInput) -> CreateObservationCreateObservation:
        """
        Publish the Observations to OMS
        """
        return self.oms_client.create_observation(observation_input)

    def create_relationship(self, relationship_input: CreateRelationshipInput) -> CreateRelationshipCreateRelationship:
        """
        Publish the relationship to OMS
        :param relationship_input: a CreateRelationshipInput object
        """
        # 1. for each relationship, publish it to OMS
        return self.oms_client.create_relationship(relationship_input)

    def create_attribute(self, attribute_input: CreateAttributeInput) -> CreateAttributeCreateAttribute:
        """
        Publish the attribute to oms
        :param attribute_input: a CreateAttributeInput object
        """
        # 1. for each attribute, publish it to OMS
        return self.oms_client.create_attribute(attribute_input)

    def create_activity(self, activity_input: CreateActivityInput) -> CreateActivityCreateActivity:
        """
        Publish the activity to oms
        :param activity_input: a CreateActivityInput object
        """
        # 1. for each activity, publish it to OMS
        return self.oms_client.create_activity(activity_input)

    def create_source(self, source_input: CreateSourceInput) -> CreateSourceCreateSource:
        """
        Create a source in OMS
        :param source_input: a CreateSourceInput object
        """
        return self.oms_client.create_source(source_input)

    def create_provider(self, provider_input: CreateProviderInput) -> CreateProviderCreateProvider:
        """
        Create a provider in OMS
        :param provider_input: a CreateProviderInput object
        """
        return self.oms_client.create_provider(provider_input)

    def create_originator(self, originator_input: CreateOriginatorInput) -> CreateOriginatorCreateOriginator:
        """
        Create an Originator in OMS
        :param originator_input: a CreateOriginatorInput object
        """
        return self.oms_client.create_originator(originator_input)

    ### GET ###
    def get_activity(self, id: UUID) -> ActivityActivity:
        """Get existing Activity from OMS"""
        activity = self.oms_client.activity(IdQuery(id=id))
        return activity

    @cached(TTLCache(SETTINGS.oms_crud_ttl_cache_size, SETTINGS.oms_crud_ttl_cache_seconds))
    def get_attribute(self, id: UUID) -> AttributeAttribute:
        """Get existing Attribute from OMS"""
        attribute = self.oms_client.attribute(IdQuery(id=id))
        return attribute

    @cached(TTLCache(SETTINGS.oms_crud_ttl_cache_size, SETTINGS.oms_crud_ttl_cache_seconds))
    def get_node(self, id: UUID) -> NodeNode:
        """Get existing Node from OMS"""
        node = self.oms_client.node(IdQuery(id=id))
        return node

    @cached(TTLCache(SETTINGS.oms_crud_ttl_cache_size, SETTINGS.oms_crud_ttl_cache_seconds))
    def get_observation(self, id: UUID) -> ObservationObservation:
        """Get existing Observation from OMS"""
        observation = self.oms_client.observation(IdQuery(id=id))
        return observation

    def get_nodes(self, node_info: NodeQuery) -> NodesNodes:
        """Get existing Node from OMS"""
        # enforce pagination bounds if configured
        self._ensure_pagination_params(node_info)
        nodes = self.oms_client.nodes(query=node_info)
        LOGGER.debug("GraphQL nodes fetched: %d", len(nodes.data or []))
        return nodes

    def get_relationships(self, relationship_info: RelationshipQuery) -> RelationshipsRelationships:
        """Get existing Relationships from OMS"""
        self._ensure_pagination_params(relationship_info)
        relationships = self.oms_client.relationships(query=relationship_info)
        LOGGER.debug("GraphQL relationships fetched: %d", len(relationships.data or []))
        return relationships

    def get_attributes(self, attribute_info: AttributeQuery) -> AttributesAttributes:
        """Get existing Attributes from OMS"""
        self._ensure_pagination_params(attribute_info)
        attributes = self.oms_client.attributes(query=attribute_info)
        LOGGER.debug("GraphQL attributes fetched: %d", len(attributes.data or []))
        return attributes

    def get_activities(self, activity_info: ActivityQuery) -> ActivitiesActivities:
        """Get existing Activities from OMS"""
        self._ensure_pagination_params(activity_info)
        activities = self.oms_client.activities(query=activity_info)
        LOGGER.debug("GraphQL activities fetched: %d", len(activities.data or []))
        return activities

    def get_observations(self, observation_info: ObservationQuery) -> ObservationsObservations:
        """Get existing Observations from OMS"""
        self._ensure_pagination_params(observation_info)
        observations = self.oms_client.observations(query=observation_info)
        LOGGER.debug("GraphQL observations fetched: %d", len(observations.data or []))
        return observations

    def get_source(self, source_id: str) -> SourceSource:
        """Get existing Attributes from OMS"""
        source = self.oms_client.source(query=IdQuery(id=source_id))
        return source

    def get_source_by_name(self, source_name: str) -> SourcesSources:
        return self.oms_client.sources(query=SourceQuery(name=StringQuery(equals=source_name)))

    def get_provider_by_name(self, provider_name: str) -> ProvidersProviders:
        """Get existing Attributes from OMS"""
        return self.oms_client.providers(query=ProviderQuery(name=StringQuery(equals=provider_name)))

    def get_originator_by_name(self, originator_name: str) -> OriginatorsOriginators:
        """Get existing Attributes from OMS"""
        return self.oms_client.originators(query=OriginatorQuery(name=StringQuery(equals=originator_name)))

    def get_pages_of_activities(self, name: str, node: NodeNode, pagesize: int = 200) -> list[ActivitiesActivities]:
        activities: list[ActivitiesActivities] = []
        page = 1
        while True:
            activity_query = ActivityQuery(
                name=StringQuery(equals=name),
                nodeIds=UuidQueryByList(in_=[node.id]),
                pageParams=PageParams(page=page, pageSize=pagesize),
            )
            activity_response = self.get_activities(activity_query)
            activities_page = activity_response.data
            if not activities_page:
                break
            activities.extend(activities_page)
            if len(activities_page) < pagesize:
                break
            page += 1
        return activities

    ### UPDATE ###
    def update_node(self, update_input: UpdateNodeInput) -> UpdateNodeUpdateNode:
        """Update node"""
        return self.oms_client.update_node(update_input)

    def update_relationship(self, update_input: UpdateRelationshipInput) -> UpdateRelationshipUpdateRelationship:
        """Update relationship"""
        return self.oms_client.update_relationship(update_input)

    def update_attribute(self, update_input: UpdateAttributeInput) -> UpdateAttributeUpdateAttribute:
        """Update attribute"""
        return self.oms_client.update_attribute(update_input)

    def update_source(self, update_input: UpdateSourceInput) -> UpdateSourceUpdateSource:
        """Update source"""
        return self.oms_client.update_source(update_input)

    def update_activity(self, update_input: UpdateActivityInput) -> UpdateActivityUpdateActivity:
        """Update activity"""
        return self.oms_client.update_activity(update_input)

    ### DELETE ###
    def delete_node(self, node_id: str) -> bool:
        """Update node"""
        return self.oms_client.delete_node(DeleteByIdInput(id=node_id))

    def delete_relationship(self, relationship_id: str) -> bool:
        """Update relationship"""
        return self.oms_client.delete_relationship(DeleteByIdInput(id=relationship_id))

    def delete_attribute(self, attribute_id: str) -> bool:
        """Update attribute"""
        return self.oms_client.delete_attribute(DeleteByIdInput(id=attribute_id))

    def delete_provider(self, provider_id: str) -> bool:
        return self.oms_client.delete_provider(DeleteByIdInput(id=provider_id))

    def delete_originator(self, originator_id: str) -> bool:
        return self.oms_client.delete_originator(DeleteByIdInput(id=originator_id))

    def delete_source(self, source_id) -> bool:
        return self.oms_client.delete_source(DeleteByIdInput(id=source_id))

    def delete_observation(self, observation_id) -> bool:
        return self.oms_client.delete_observation(DeleteByIdInput(id=observation_id))

    def delete_activity(self, activity_id) -> bool:
        return self.oms_client.delete_activity(DeleteByIdInput(id=activity_id))

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

    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        """Get the Ontology Class for a given iri

        :param iri: Iri to get ontology data for
        :return: Optional OntologyClass object
        """
        warnings.warn("This method is deprecated, use the Ontology Client instead", stacklevel=2)
        return self.oms_client.ontology_class(query=IriQuery(iri=iri))
