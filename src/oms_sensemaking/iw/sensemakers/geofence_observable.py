import json
import logging
from datetime import datetime, timedelta
from typing import List, Literal
from zoneinfo import ZoneInfo

from oms_sdk.generated.generated_graphql_client import GeoQuery, GeoQueryType, ObservationQuery, TimeQuery
from oms_sdk.generated.generated_graphql_client.input_types import AttributeQuery
from pydantic import BaseModel

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.iw.sensemakers.base_observable import BaseObservable

LOGGER: logging.Logger = logging.getLogger(__name__)


class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]]  # [[[lon, lat], [lon, lat], ...]]

    class Config:
        extra = "allow"


class GeofenceObservable(BaseObservable):
    location: GeoJSONPolygon

    def update_data(self):
        """Update data for geofence observable."""
        self.ensure_initialized()
        # get status attribute
        status_attr = self.get_status_attr()
        if not status_attr:
            LOGGER.error(f"No status attribute found for observable {self.id}")
            return

        # get related object IDs
        related_ids = self.get_related_object_ids()
        related_ids = related_ids if related_ids else []
        total = len(set(related_ids))

        if total == 0:
            LOGGER.info(f"No related objects found for observable {self.id}")
            return

        def format_rfc3339(dt: datetime) -> str:
            return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # determine time query parameters
        if self.time_bounds.since_last_query:
            # TODO: query observable history DB for last query time
            # for now, just check last 15 minutes
            now = datetime.now(ZoneInfo("UTC"))
            start_time = format_rfc3339(now - timedelta(minutes=50))
            end_time = format_rfc3339(now)
        else:
            start_time = self.time_bounds.start_time
            end_time = self.time_bounds.end_time

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
            LOGGER.error(f"Unable to load geometry for observable {self.id}: {e}")
            return

        # query observations
        observations = self.oms_client.get_observations(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
            ObservationQuery(
                nodeIds={"in": related_ids},  # TODO: find out how to represent this in a typesafe way
                startTime=TimeQuery(gte=start_time),
                endTime=TimeQuery(lte=end_time),
                geometry=GeoQuery(queryGeoJson=self.location, queryType=GeoQueryType.INTERSECTS),
            )
        )

        # count unique observations
        num_observed = len(set([o.nodeId for o in observations.data])) if observations.data else 0

        # update status
        self.update_status(num_observed, total)
