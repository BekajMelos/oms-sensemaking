from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Literal, Optional

from oms_sdk.generated.generated_graphql_client import (
    AttributeQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
    UpdateAttributeInput,
)
from pydantic import BaseModel, Field, model_validator

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool


class QueryType(str, Enum):
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
        allow_population_by_field_name = True


class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [lon, lat]


class StatusCriteria(BaseModel):
    attribute_iri: str = Field(..., alias="attributeIRI")
    triggering_values: List[Any] = Field(..., alias="triggeringValues")

    class Config:
        allow_population_by_field_name = True


class BaseObservable(BaseModel):
    query_type: QueryType = Field(..., alias="queryType")
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

    @model_validator(mode="after")
    def validate_observed_thresholds(self) -> "BaseObservable":
        if self.fully_observed_count is None and self.fully_observed_percentage is None:
            raise ValueError("At least one of fullyObservedCount or fullyObservedPercentage is required")

        return self

    class Config:
        allow_population_by_field_name = True

    def update_data(self):
        """Base method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement update_data()")

    def get_status_attr(self):
        """Get the status attribute for this observable."""
        if not self.oms_client or not self.id:
            raise ValueError("oms_client and id must be set")

        status_attr = self.oms_client.get_attributes(
            AttributeQuery(nodeIds=[self.id], attributeIris=[SETTINGS.iw_settings.observable_status_attribute_iri])
        )
        if status_attr.data:
            self.status_attribute_id = status_attr.data[0].id
            return status_attr.data[0]
        return None

    def get_related_object_ids(self):
        """Get related object IDs for this observable."""
        if not self.oms_client or not self.id:
            raise ValueError("oms_client and id must be set")

        relationships = self.oms_client.get_relationships(
            RelationshipQuery(
                nodes=RelationshipNodeQuery(nodeIds=[self.id]),
                objectPropertyIris=[SETTINGS.iw_settings.observable_associated_with_relationship_iri],
            )
        )
        self.related_object_ids = [rel.endNodeId for rel in relationships.data]
        return self.related_object_ids

    def update_status(self, num_observed, total):
        """Update the status attribute based on observation counts."""
        if not self.oms_client or not self.status_attribute_id:
            raise ValueError("oms_client and status_attribute_id must be set")

        updated_status = None
        if num_observed == 0:
            updated_status = SETTINGS.iw_settings.observable_statuses["not_observed"]
        elif num_observed == total:
            updated_status = SETTINGS.iw_settings.observable_statuses["observed"]
        elif num_observed < total and num_observed > 0:
            updated_status = SETTINGS.iw_settings.observable_statuses["partially_observed"]
        else:
            updated_status = SETTINGS.iw_settings.observable_statuses["unknown"]

        self.oms_client.update_attribute(
            UpdateAttributeInput(
                id=self.status_attribute_id,
                attributeValue=updated_status,
                attributeDisplayValue=updated_status,
                attributeNormalizedValue=updated_status,
                isUserEntered=False,
                labels=[SETTINGS.sm_inferenced_label],
            )
        )
