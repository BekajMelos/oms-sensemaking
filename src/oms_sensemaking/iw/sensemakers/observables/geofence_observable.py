import json
import logging
from typing import List, Literal

from oms_sdk.generated.generated_graphql_client import GeoQuery, GeoQueryType, ObservationQuery, TimeQuery
from oms_sdk.generated.generated_graphql_client.input_types import AttributeQuery
from pydantic import BaseModel, ConfigDict

from oms_sensemaking.config import SETTINGS

from .base_observable import BaseObservable

LOGGER: logging.Logger = logging.getLogger(__name__)


class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]]  # [[[lon, lat], [lon, lat], ...]]

    model_config = ConfigDict(extra="allow")


class GeofenceObservable(BaseObservable):
    location: GeoJSONPolygon

    def update_data(self):
        """Update data for geofence observable."""
        self.ensure_initialized()
        # get status attribute
        status_attr = self.get_status_attr()
        if not status_attr:
            LOGGER.error("No status attribute found for observable %s", self.id)
            return

        # get related object IDs
        related_ids = self.get_related_object_ids()
        related_ids = set(related_ids) if related_ids else []
        total = len(related_ids)

        # get geometry
        try:
            self.location = json.loads(
                self.oms_client.get_attributes(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                    AttributeQuery(
                        nodeIds=[self.id], attributeIris=[SETTINGS.iw_settings.observable_config_attribute_iri]
                    )
                )
                .data[0]
                .attributeValue
            )["location"]

        except Exception as e:
            LOGGER.error("Unable to load geometry for observable %s: %s", self.id, e)
            return

        # get number of objects observed within bounds
        num_objects_observed = sum(
            len(
                self.oms_client.get_observations(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                    ObservationQuery(
                        nodeIds={"in": [o_id]},
                        startTime=TimeQuery(gte=self.time_bounds.start_time),
                        endTime=TimeQuery(lte=self.time_bounds.end_time),
                        geometry=GeoQuery(queryGeoJson=self.location, queryType=GeoQueryType.INTERSECTS),
                    )
                ).data
            )
            > 0
            for o_id in related_ids
        )

        # update status
        self.update_status(num_objects_observed, total)
