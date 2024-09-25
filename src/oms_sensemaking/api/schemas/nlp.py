"""Schemas representing the input and output formats for the NLP sensemaker."""

from oms_sdk import DEFAULT_ACM
from pydantic import BaseModel, Field


class NlpRequest(BaseModel):
    """Represents a request to the NLP sensemaker."""

    acm: dict = Field(..., description="The ACM for the associated data.", examples=[DEFAULT_ACM])
    source_id: str = Field(
        ..., description="The SourceID of the Source associated with the submitted text.", examples=["id1"]
    )
    text: str = Field(
        ..., description="The text to analyze.", examples=["The quick brown fox jumps over the lazy dog."]
    )


class NlpResponse(BaseModel):
    """Represents a request to the NLP sensemaker."""

    acm: dict = Field(..., description="The ACM for the associated data.", examples=[DEFAULT_ACM])
    source_id: str = Field(
        ..., description="The SourceID of the Source associated with the submitted text.", examples=["id1"]
    )
    findings: dict = Field(..., description="The entities and relationships extracted from the text.", examples=[{}])
