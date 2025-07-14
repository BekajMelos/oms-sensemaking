from pprint import pprint

from oms_sdk.generated.generated_graphql_client import (
    AttributeQuery,
    GeoQuery,
    GeoQueryType,
    NodeQuery,
    ObservationQuery,
    PageParams,
    RelationshipNodeQuery,
    RelationshipQuery,
    TimeQuery,
    UpdateAttributeInput,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

# class IWGeospatialSensemaker:
#     def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
#         """Create a new instance of IWGeospatialSensemaker."""
#         super().__init__()
#         self.version = (0, 0, 1)
#         self.oms_crud_tool = oms_crud_tool

#     def process_data(self, )


def get_observables(oms_client):
    return oms_client.get_nodes(NodeQuery(tags=["observable"], pageParams=PageParams(pageSize=1)))


def get_location_attr(oms_client, observable_id):
    return oms_client.get_attributes(
        AttributeQuery(nodeIds=[observable_id], attributeIris=[SETTINGS.iw_settings.observable_location_attribute_iri])
    )[0]


def get_status_attr(oms_client, observable_id):
    return oms_client.get_attributes(
        AttributeQuery(nodeIds=[observable_id], attributeIris=[SETTINGS.iw_settings.observable_status_attribute_iri])
    )[0]


def get_related_object_ids(oms_client, observable_id):
    relationships = oms_client.get_relationships(
        RelationshipQuery(
            nodes=RelationshipNodeQuery(nodeIds=[observable_id]),
            objectPropertyIris=[SETTINGS.iw_settings.observable_associated_with_relationship_iri],
        )
    )
    return [rel.endNodeId for rel in relationships.data]


# def get_observations(oms_client, )


if __name__ == "__main__":
    print("1!!!!!!!!!!!")
    oms_client = OmsCrudTool()
    print("2!!!!!!!!!!!")
    observable_query = NodeQuery(tags=["observable"], pageParams=PageParams(pageSize=1))
    print("3!!!!!!!!!!!")

    observables = oms_client.get_nodes(observable_query)
    print("4!!!!!!!!!!!")
    print("observables:")
    # pprint(observables.en
    print()

    location_attribute = oms_client.get_attributes(
        AttributeQuery(
            nodeIds=[observables.data[0].id], attributeIris=[SETTINGS.iw_settings.observable_location_attribute_iri]
        )
    )
    print("loc attr:")
    pprint(location_attribute, indent=2)
    print()
    status_attribute = oms_client.get_attributes(
        AttributeQuery(
            nodeIds=[observables.data[0].id], attributeIris=[SETTINGS.iw_settings.observable_status_attribute_iri]
        )
    )
    print("status attr:")
    pprint(status_attribute, indent=2)
    print()
    status_attribute_id = status_attribute.data[0].id

    relationships = oms_client.get_relationships(
        RelationshipQuery(
            nodes=RelationshipNodeQuery(nodeIds=[observables.data[0].id]),
            objectPropertyIris=[SETTINGS.iw_settings.observable_associated_with_relationship_iri],
        )
    )
    print("rels:")
    pprint(relationships)
    print()

    related_object_ids = [rel.endNodeId for rel in relationships.data]
    total = len(set(related_object_ids))
    print("rel obj ids:")
    pprint(related_object_ids)
    print()

    observations = oms_client.get_observations(
        ObservationQuery(
            nodeIds={"in": related_object_ids},
            startTime=TimeQuery(gt="2025-07-01T16:29:00+00:00"),
            endTime=TimeQuery(lte="2025-07-15T16:30:00+00:00"),
            geometry=GeoQuery(queryGeoJson=location_attribute.data[0].geometry, queryType=GeoQueryType.INTERSECTS),
        )
    )
    print("observations:")
    pprint(observations.data.location for obs in observations)
    print()

    num_observed = len(set([o.nodeId for o in observations.data]))

    updated_status = None  # TODO: maybe instead, get the existing_status attribute and update it directly
    if num_observed == 0:
        updated_status = SETTINGS.iw_settings.observable_statuses["not_observed"]
    elif num_observed == total:
        updated_status = SETTINGS.iw_settings.observable_statuses["observed"]
    elif num_observed < total and num_observed > 0:
        updated_status = SETTINGS.iw_settings.observable_statuses["partially_observed"]
    else:
        updated_status = SETTINGS.iw_settings.observable_statuses["unknown"]

    oms_client.update_attribute(
        UpdateAttributeInput(
            id=status_attribute_id,
            attributeValue=updated_status,
            attributeDisplayValue=updated_status,
            attributeNormalizedValue=updated_status,
            isUserEntered=False,
            labels=[
                SETTINGS.sm_inferenced_label,
            ],
        )
    )
