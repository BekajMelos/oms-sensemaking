"""Schemas representing the input and output formats for the NLP sensemaker."""

from pydantic import BaseModel, Field

from oms_sensemaking.core.schemas import SecurityMixin, SourceMixin


class NlpRequest(SecurityMixin, SourceMixin, BaseModel):
    """Represents a request to the NLP sensemaker."""

    text: str = Field(
        ..., description="The text to analyze.", examples=["The quick brown fox jumps over the lazy dog."]
    )


class NlpResponse(SecurityMixin, SourceMixin, BaseModel):
    """Represents a request to the NLP sensemaker."""

    findings: dict = Field(..., description="The entities and relationships extracted from the text.", examples=[{}])
