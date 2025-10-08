import json
import logging
from typing import Any, List

from oms_sdk.generated.generated_graphql_client.input_types import AttributeQuery, StringQuery
from pydantic import BaseModel, Field, TypeAdapter

from oms_sensemaking.config import SETTINGS

from .base_observable import BaseObservable

LOGGER: logging.Logger = logging.getLogger(__name__)


class StatusCriteria(BaseModel):
    attribute_iri: str = Field(..., alias="attributeIri")
    triggering_values: List[Any] = Field(..., alias="triggeringValues")

    class Config:
        populate_by_name = True


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
        related_ids = related_ids if related_ids else []
        if len(related_ids) < 1:
            LOGGER.info(f"No related objects found for observable {self.id}")
            return

        all_ids = set(related_ids)
        filtered_ids = all_ids.copy()
        LOGGER.info("initial filtered_ids")
        LOGGER.info(filtered_ids)

        # get criteria
        try:
            raw_data = json.loads(
                self.oms_client.get_attributes(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                    AttributeQuery(
                        nodeIds=[self.id], attributeIris=[SETTINGS.iw_settings.observable_config_attribute_iri]
                    )
                )
                .data[0]
                .attributeValue
            )["criteria"]
            self.criteria = TypeAdapter(List[StatusCriteria]).validate_python(raw_data)

        except Exception as e:
            LOGGER.error(f"Unable to load criteria for observable {self.id}: {e}")
            return

        # loop through each criterion
        for criterion in self.criteria:
            # store IDs that match any triggering value for THIS criterion.
            ids_matching_this_criterion = set()

            # for the current criterion, check all its triggering values.
            for val in criterion.triggering_values:
                attributes = self.oms_client.get_attributes(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                    AttributeQuery(
                        nodeIds=related_ids,
                        attributeIris=[criterion.attribute_iri],
                        attributeValue=StringQuery(equals=val),
                    )
                ).data

                # get the IDs that matched this specific value, add them to the set for this criterion
                ids_for_this_value = {data.nodeId for data in attributes}
                ids_matching_this_criterion.update(ids_for_this_value)

            # update the main filtered list.
            filtered_ids.intersection_update(ids_matching_this_criterion)

        # update status
        self.update_status(len(filtered_ids), len(all_ids))
