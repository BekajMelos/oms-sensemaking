"""Schemas representing metadata about the application."""
from pydantic import BaseModel, Field


class AppInfo(BaseModel):
    """Provides metadata about an application."""

    title: str = Field(..., examples=["OMS Sensemaking Service"])
    version: str = Field(..., examples=["1.2.3"])
    description: str = Field(..., examples=["A service for performing analytics on OMS data."])
