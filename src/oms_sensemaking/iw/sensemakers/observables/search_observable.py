import json
import logging
from typing import List

from oms_sdk.generated.generated_graphql_client import ObservationQuery, TimeQuery
from oms_sdk.generated.generated_graphql_client.input_types import AttributeQuery

from oms_sensemaking.config import SETTINGS

from .base_observable import BaseObservable, StatusCriteria

LOGGER: logging.Logger = logging.getLogger(__name__)


class SearchObservable(BaseObservable):
    criteria: List[StatusCriteria]

    def update_data(self):
        """Update data for search observable."""

        self.ensure_initialized()
        # get status attribute
        status_attr = self.get_status_attr()
        if not status_attr:
            LOGGER.error(f"No status attribute found for observable {self.id}")
            return

        # get related object IDs
        related_ids = self.get_related_object_ids()
        related_ids = set(related_ids) if related_ids else []
        total = len(related_ids)

        # get criteria
        try:
            self.criteria = json.loads(
                self.oms_client.get_attributes(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                    AttributeQuery(
                        nodeIds=[self.id], attributeIris=[SETTINGS.iw_settings.observable_config_attribute_iri]
                    )
                )
                .data[0]
                .attributeValue
            )["criteria"]

        except Exception as e:
            LOGGER.error(f"Unable to load geometry for observable {self.id}: {e}")
            return

        # get number of objects that meet criteria
        non_node_params = {
            "startTime": TimeQuery(gte=self.time_bounds.start_time),
            "endTime": TimeQuery(lte=self.time_bounds.end_time),
            # TODO: criteria here
        }
        print(non_node_params)

        num_objects_observed = sum(
            len(
                self.oms_client.get_observations(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                    ObservationQuery(
                        nodeIds={"in": related_ids},
                    )
                ).data
            )
            for o_id in related_ids
            if total > 0
        )

        # update status
        self.update_status(num_objects_observed, total)
