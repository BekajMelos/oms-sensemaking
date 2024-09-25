"""Schemas representing OMS objects."""
import uuid
from typing import Any, Optional

from pydantic import UUID4, BaseModel, Field, field_serializer


class OmsObject(BaseModel):
    """Represents an "object" in OMS."""
    id: UUID4 = Field(..., examples=["63a17206-8d4d-4825-9b0e-958cf54fa639"])

    version: int = Field(..., examples=[1])

    acm: dict = Field(..., examples=[{
        "version": "2.1.0",
        "classif": "U",
        "owner_prod": ["USA"],
        "atom_energy": [],
        "sar_id": [],
        "sci_ctrls": [],
        "disponly_to": [""],
        "dissem_ctrls": [],
        "non_ic": [],
        "rel_to": [],
        "fgi_open": [],
        "fgi_protect": [],
        "portion": "U",
        "banner": "UNCLASSIFIED",
        "dissem_countries": ["USA"],
        "accms": [],
        "macs": [],
        "oc_attribs": [{"orgs": [], "missions": [], "regions": []}],
        "f_clearance": ["u"],
        "f_sci_ctrls": [],
        "f_accms": [],
        "f_oc_org": [],
        "f_regions": [],
        "f_missions": [],
        "f_share": [],
        "f_sar_id": [],
        "f_atom_energy": [],
        "f_macs": [],
        "disp_only": "",
    }])

    tags: Optional[list[str]] = None

    @field_serializer('id')
    def serialize_uuid(self, val: uuid.UUID) -> str:
        """
        Serializes a UUID to a string.

        :param val: The value to serialize.
        :return: A string representation of a UUID.
        """
        return str(val)


class Attribute(OmsObject):
    """Represents an Attribute object in OMS."""

    attribute_iri: str = Field(..., examples=["https://foundry.ai.mil/DICO/v3.1.0/Common_Name"])
    attribute_name: str = Field(..., examples=["Common Name"])
    attribute_value: Any


class Node(OmsObject):
    """Represents a Node object in OMS."""

    id: UUID4
    version: str # change to Long type
    acm: str # change to ACM type
    #tags: list[str]
    tags: str
    guideID: str
    name: str
    tier: str # change to object type
    classIri: str
    className: str
    #ifcCodes: list[str]
    ifcCodes: str
    allegiance: str
    allegianceAor: str
    currentAor: str
    isNso: bool
    #class_iri: str = Field(..., examples=["http://purl.obolibrary.org/obo/BFO_0000030"])
    #class_name: str = Field(..., examples=["Object"])


class Relationship(OmsObject):
    """Represents an Attribute object in OMS."""

    name: str

    start_node_id: UUID4 = Field(..., examples=["63a17206-8d4d-4825-9b0e-958cf54fa639"])

    end_node_id: UUID4 = Field(..., examples=["4d93fac7-5659-4ca9-b735-84aad702cee0"])

    object_property_iri: str = Field(
        ...,
        examples=["http://schema.dia.mil/DefenseIntelligenceCoreOntology/objectCreator"]
    )

    object_property_name: str = Field(..., examples=["Object Creator"])

    @field_serializer('id', 'start_node_id', 'end_node_id')
    def serialize_uuid(self, val: uuid.UUID) -> str:
        """
        Serializes a UUID to a string.

        :param val: The value to serialize.
        :return: A string representation of a UUID.
        """
        return super().serialize_uuid(val)


class CreateObjectResponse(BaseModel):
    """Represents the response for object "create" endpoints."""

    print("**********CREATE OBJECT RESPONSE************")
    success: bool = Field(
        ...,
        examples=[True],
        description="Indicates if the object was successfully created in the graph."
    )
    print(success)
    print("**********END CREATE RESPONSE**********")


class DeleteObjectResponse(BaseModel):
    """Represents the response for object "delete" endpoints."""

    success: bool = Field(
        ...,
        examples=[True],
        description="Indicates if the object was successfully deleted from the graph."
    )
