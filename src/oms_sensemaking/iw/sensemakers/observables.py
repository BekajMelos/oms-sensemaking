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

# class GeospatialObservableSensemaker:

#     def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
#         """Create a new instance of GeospatialObservableSensemaker."""
#         super().__init__()
#         self.version = (0, 0, 1)
#         self.oms_crud_tool = oms_crud_tool


#     def process_data(self, )

if __name__ == "__main__":
    oms_client = OmsCrudTool()
    observable_query = NodeQuery(tags=["observable"], pageParams=PageParams(pageSize=1))

    observables = oms_client.get_nodes(observable_query)

    location_attribute = oms_client.get_attributes(
        AttributeQuery(
            nodeIds=[observables.data[0].id], attributeIris=[SETTINGS.iw_settings.observable_location_attribute_iri]
        )
    )
    status_attribute = oms_client.get_attributes(
        AttributeQuery(
            nodeIds=[observables.data[0].id], attributeIris=[SETTINGS.iw_settings.observable_status_attribute_iri]
        )
    )
    status_attribute_id = status_attribute.data[0].id

    relationships = oms_client.get_relationships(
        RelationshipQuery(
            nodes=RelationshipNodeQuery(nodeIds=[observables.data[0].id]),
            objectPropertyIris=[SETTINGS.iw_settings.observable_associated_with_relationship_iri],
        )
    )

    related_object_ids = [rel.endNodeId for rel in relationships.data]
    total = len(set(related_object_ids))

    observations = oms_client.get_observations(
        ObservationQuery(
            nodeIds={"in": related_object_ids},
            startTime=TimeQuery(gt="2025-07-01T16:29:00+00:00"),
            endTime=TimeQuery(lte="2025-07-01T16:30:00+00:00"),
            geometry=GeoQuery(queryGeoJson=location_attribute.data[0].geometry, queryType=GeoQueryType.INTERSECTS),
        )
    )

    # TODO: fix this logic: actually need to check the number of objects observed
    num_observed = len(set([o.id for o in observations.data]))

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
