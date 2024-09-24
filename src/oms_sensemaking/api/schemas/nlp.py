"""Schemas representing the input and output formats for the NLP sensemaker."""

from oms_sdk import DEFAULT_ACM
from pydantic import BaseModel, Field


class NlpRequest(BaseModel):
    """Represents a request to the NLP sensemaker."""

    acm: dict = Field(..., description="The ACM for the associated data.", examples=[DEFAULT_ACM])
    text: str = Field(
        ..., description="The text to analyze.", examples=["The quick brown fox jumps over the lazy dog."]
    )
    # TODO: add request definition ehre


class NlpResponse(BaseModel):
    """Represents a request to the NLP sensemaker."""

    acm: dict = Field(..., description="The ACM for the associated data.", examples=[DEFAULT_ACM])
    # TODO: add response definition ehre
