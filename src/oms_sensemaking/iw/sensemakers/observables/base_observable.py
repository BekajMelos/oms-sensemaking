from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional, Union
from zoneinfo import ZoneInfo

from oms_sdk.generated.generated_graphql_client import (
    AttributeQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
    UpdateAttributeInput,
)
from pydantic import BaseModel, Field, model_validator

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)


class ObservableQueryType(Enum):
    GEOFENCE = "geoFence"
    SEARCH = "search"


def format_rfc3339(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class TimeBounds(BaseModel):
    since_last_query: Optional[bool] = Field(None, alias="sinceLastQuery")
    start_time: Optional[Union[datetime, str]] = Field(None, alias="startTime")
    end_time: Optional[Union[datetime, str]] = Field(None, alias="endTime")

    @model_validator(mode="after")
    def validate_time_bounds(self) -> "TimeBounds":
        if not self.since_last_query:
            if self.start_time is None or self.end_time is None:
                raise ValueError("startTime and endTime are required when sinceLastQuery is False")
        else:
            now = datetime.now(ZoneInfo("UTC"))
            # TODO: query observable history DB for last query time
            # for now, just check according to settings query interval
            self.start_time = format_rfc3339(now - SETTINGS.iw_settings.observable_query_interval)
            self.end_time = format_rfc3339(now)

        return self

    class Config:
        populate_by_name = True


class BaseObservable(BaseModel):
    query_type: ObservableQueryType = Field(..., alias="queryType")
    time_bounds: TimeBounds = Field(..., alias="timeBounds")
    class_iris: Optional[List[str]] = Field(None, alias="classIRIs")

    # observation thresholds - at least one is required
    none_observed_count: Optional[int] = Field(None, alias="noneObservedCount")
    partially_observed_count: Optional[int] = Field(None, alias="partiallyObservedCount")
    fully_observed_count: Optional[int] = Field(None, alias="fullyObservedCount")
    none_observed_percentage: Optional[float] = Field(None, alias="noneObservedPercentage", ge=0.0, le=100.0)
    partially_observed_percentage: Optional[float] = Field(None, alias="partiallyObservedPercentage", ge=0.0, le=100.0)
    fully_observed_percentage: Optional[float] = Field(None, alias="fullyObservedPercentage", ge=0.0, le=100.0)

    # object properties for instance use
    id: Optional[str] = None
    status_attribute_id: Optional[str] = None
    related_object_ids: Optional[List[str]] = None
    oms_client: Optional[OmsCrudTool] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

    def initialize(self, id: str, oms_client: OmsCrudTool) -> "BaseObservable":
        """Initialize the observable with required runtime properties."""
        self.id = id
        self.oms_client = oms_client
        return self

    def ensure_initialized(self) -> None:
        """Ensure the observable is properly initialized."""
        if not self.oms_client or not self.id:
            raise ValueError("Observable is not properly initialized with oms_client or id. Call initialize() first.")

    @model_validator(mode="after")
    def validate_observed_thresholds(self) -> "BaseObservable":
        if self.fully_observed_count is None and self.fully_observed_percentage is None:
            raise ValueError("At least one of fullyObservedCount or fullyObservedPercentage is required")

        return self

    def update_data(self):
        """Base method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement update_data()")

    def get_status_attr(self):
        """Get the status attribute for this observable."""
        self.ensure_initialized()
        status_attr = self.oms_client.get_attributes(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
            AttributeQuery(nodeIds=[self.id], attributeIris=[SETTINGS.iw_settings.observable_status_attribute_iri])
        )
        if status_attr.data:
            self.status_attribute_id = status_attr.data[0].id
            return status_attr.data[0]
        return None

    def get_related_object_ids(self):
        """Get related object IDs for this observable."""
        self.ensure_initialized()
        relationships = self.oms_client.get_relationships(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
            RelationshipQuery(
                nodes=RelationshipNodeQuery(nodeIds=[self.id]),
                objectPropertyIris=[SETTINGS.iw_settings.observable_associated_with_relationship_iri],
            )
        )
        self.related_object_ids = [rel.endNodeId for rel in relationships.data]
        return self.related_object_ids

    def determine_status(self, num_observed, total):
        """Determine status based on configured thresholds."""

        percentage_observed = 0 if total == 0 else num_observed / total * 100

        # priority of checking can be adjusted here

        # check fully observed threshold
        if (self.fully_observed_count is not None and num_observed >= self.fully_observed_count) or (
            self.fully_observed_percentage is not None and percentage_observed >= self.fully_observed_percentage
        ):
            return SETTINGS.iw_settings.observable_statuses["fully_observed"]

        # check partially observed threshold
        if (self.partially_observed_count is not None and num_observed >= self.partially_observed_count) or (
            self.partially_observed_percentage is not None and percentage_observed >= self.partially_observed_percentage
        ):
            return SETTINGS.iw_settings.observable_statuses["partially_observed"]

        # check none observed threshold
        else:
            return SETTINGS.iw_settings.observable_statuses["not_observed"]

    def update_status(self, num_observed, total):
        """Update the status attribute based on observation counts."""
        self.ensure_initialized()

        LOGGER.info(f"Observed {num_observed} of {total} objects which met criteria for observable {self.id}")

        prev_status = self.get_status_attr()
        prev_status_value = prev_status.attributeValue if prev_status else ""
        new_status_value = self.determine_status(num_observed, total)

        if prev_status_value != new_status_value:
            self.oms_client.update_attribute(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
                UpdateAttributeInput(
                    id=self.status_attribute_id,
                    attributeValue=new_status_value,
                    attributeDisplayValue=new_status_value,
                    attributeNormalizedValue=new_status_value,
                    isUserEntered=False,
                    labels=[SETTINGS.sm_inferenced_label],
                )
            )

            LOGGER.info(
                f"Updated status{" from " + prev_status_value}"
                f" to {new_status_value} "
                f"for {self.query_type} observable {self.id}"
            )

        else:
            LOGGER.info(f"Status for {self.query_type} observable " f"{self.id} remained as {prev_status_value}")
