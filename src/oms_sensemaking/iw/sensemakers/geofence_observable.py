from datetime import datetime, timedelta
from typing import List, Literal

from oms_sdk.generated.generated_graphql_client import (
    GeoQuery,
    GeoQueryType,
    ObservationQuery,
    TimeQuery,
)
from pydantic import BaseModel

from oms_sensemaking.iw.sensemakers.base_observable import BaseObservable


class GeoJSONPolygon(BaseModel):
    type: Literal["Polygon"] = "Polygon"
    coordinates: List[List[List[float]]]  # [[[lon, lat], [lon, lat], ...]]


class GeofenceObservable(BaseObservable):
    location: GeoJSONPolygon

    def update_data(self):
        """Update data for geofence observable."""
        self.ensure_initialized()
        # get status attribute
        status_attr = self.get_status_attr()
        if not status_attr:
            print(f"No status attribute found for observable {self.id}")
            return

        # get related object IDs
        related_ids = self.get_related_object_ids()
        related_ids = related_ids if related_ids else []
        total = len(set(related_ids))

        if total == 0:
            print(f"No related objects found for observable {self.id}")
            return

        # determine time query parameters
        if self.time_bounds.since_last_query:
            # TODO: query observable history DB for last query time
            # for now, just check last 15 minutes
            start_time = (datetime.now() - timedelta(minutes=15)).isoformat()
            end_time = datetime.now().isoformat()
        else:
            start_time = self.time_bounds.start_time.isoformat()
            end_time = self.time_bounds.end_time.isoformat()

        # query observations
        observations = self.oms_client.get_observations(
            ObservationQuery(
                nodeIds={"in": related_ids},
                startTime=TimeQuery(gt=start_time),
                endTime=TimeQuery(lte=end_time),
                geometry=GeoQuery(queryGeoJson=self.location.dict(), queryType=GeoQueryType.INTERSECTS),
            )
        )

        # count unique observations
        num_observed = len(set([o.nodeId for o in observations.data])) if observations.data else 0

        # update status
        self.update_status(num_observed, total)
