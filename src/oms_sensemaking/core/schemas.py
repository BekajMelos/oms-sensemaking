from oms_sdk import DEFAULT_ACM
from pydantic import BaseModel, Field


class SourceMixin(BaseModel):
    """Source metadata."""

    source_id: str = Field(
        ..., description="The SourceID of the Source associated with the submitted text.", examples=["id1"]
    )


class SecurityMixin(BaseModel):
    """Security marking attributes."""

    acm: dict = Field(..., description="The ACM for the associated data.", examples=[DEFAULT_ACM])
