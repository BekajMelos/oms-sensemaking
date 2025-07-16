from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

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


class ObservableQueryType(str, Enum):
    GEOFENCE = "geofence"
    MIN_DISTANCE = "minDistance"
    STATUS = "status"
    SEARCH = "search"


class TimeBounds(BaseModel):
    since_last_query: bool = Field(..., alias="sinceLastQuery")
    start_time: Optional[datetime] = Field(None, alias="startTime")
    end_time: Optional[datetime] = Field(None, alias="endTime")

    @model_validator(mode="after")
    def validate_time_bounds(self) -> "TimeBounds":
        if not self.since_last_query and (self.start_time is None or self.end_time is None):
            raise ValueError("startTime and endTime are required when sinceLastQuery is False")

        return self

    class Config:
        populate_by_name = True


class StatusCriteria(BaseModel):
    attribute_iri: str = Field(..., alias="attributeIRI")
    triggering_values: List[Any] = Field(..., alias="triggeringValues")

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
    none_observed_percentage: Optional[float] = Field(None, alias="noneObservedPercentage", ge=0.0, le=1.0)
    partially_observed_percentage: Optional[float] = Field(None, alias="partiallyObservedPercentage", ge=0.0, le=1.0)
    fully_observed_percentage: Optional[float] = Field(None, alias="fullyObservedPercentage", ge=0.0, le=1.0)

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

        percentage_observed = num_observed / total

        # priority of checking can be adjusted here

        # check fully observed threshold
        if (self.fully_observed_count is not None and num_observed >= self.fully_observed_count) or (
            self.fully_observed_percentage is not None and percentage_observed >= self.fully_observed_percentage
        ):
            return SETTINGS.iw_settings.observable_statuses["observed"]

        # check partially observed threshold
        if (self.partially_observed_count is not None and num_observed >= self.partially_observed_count) or (
            self.partially_observed_percentage is not None and percentage_observed >= self.partially_observed_percentage
        ):
            return SETTINGS.iw_settings.observable_statuses["partially_observed"]

        # check none observed threshold
        if (self.none_observed_count is not None and num_observed <= self.none_observed_count) or (
            self.none_observed_percentage is not None and percentage_observed <= self.none_observed_percentage
        ):
            return SETTINGS.iw_settings.observable_statuses["not_observed"]

        # default case
        return SETTINGS.iw_settings.observable_statuses["unknown"]

    def update_status(self, num_observed, total):
        """Update the status attribute based on observation counts."""
        self.ensure_initialized()

        percentage_observed = num_observed / total

        LOGGER.info(f"Observed {num_observed} related objects of {total} for observation {self.id}")

        prev_status = self.get_status_attr()
        new_status = prev_status.attributeValue if prev_status else SETTINGS.iw_settings.observable_statuses["unknown"]

        # priority of checking can be adjusted here

        # check fully observed threshold
        if (self.fully_observed_count is not None and num_observed >= self.fully_observed_count) or (
            self.fully_observed_percentage is not None and percentage_observed >= self.fully_observed_percentage
        ):
            new_status = SETTINGS.iw_settings.observable_statuses["fully_observed"]

        # check partially observed threshold
        elif (self.partially_observed_count is not None and num_observed >= self.partially_observed_count) or (
            self.partially_observed_percentage is not None and percentage_observed >= self.partially_observed_percentage
        ):
            new_status = SETTINGS.iw_settings.observable_statuses["partially_observed"]

        # check none observed threshold
        elif (self.none_observed_count is not None and num_observed <= self.none_observed_count) or (
            self.none_observed_percentage is not None and percentage_observed <= self.none_observed_percentage
        ):
            new_status = SETTINGS.iw_settings.observable_statuses["not_observed"]

        LOGGER.info(f"Updating status from {prev_status} to {new_status} for observation {self.id}")

        self.oms_client.update_attribute(  # pyright: ignore[reportOptionalMemberAccess] - ensure_initialized has been called
            UpdateAttributeInput(
                id=self.status_attribute_id,
                attributeValue=new_status,
                attributeDisplayValue=new_status,
                attributeNormalizedValue=new_status,
                isUserEntered=False,
                labels=[SETTINGS.sm_inferenced_label],
            )
        )

        LOGGER.info(f"Updated status from {prev_status} to {new_status} for observation {self.id}")
