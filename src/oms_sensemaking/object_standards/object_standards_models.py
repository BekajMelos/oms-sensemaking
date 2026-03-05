"""Module for Object Standards Sensemaker models"""

import enum
import json
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributesData,
    RelationshipsRelationshipsData,
)
from pydantic import BaseModel, Field

from oms_sensemaking.models.sensemaking import AtomsType


class RequiredIris(BaseModel):
    """Required attribute and relationship IRIs for a rubric."""

    attribute_iris: list[str] = Field(default_factory=list)
    relationship_iris: list[str] = Field(default_factory=list)


class ViolationType(str, enum.Enum):
    """Type of Object Standards field violation."""

    MISSING = "MISSING"
    INVALID = "INVALID"


@dataclass
class FieldViolationBase:
    """
    Base class for Object Standards field violations.

    Id represents the ATOMS identifier for the field, if one exists.
    For missing fields, this will be None.
    """

    iri: str
    atoms_type: AtomsType
    violation_type: ViolationType
    description: str
    id: Optional[UUID] = None


@dataclass
class MissingFieldViolation(FieldViolationBase):
    """Represents a required field that is missing."""

    def __init__(self, iri: str, atoms_type: AtomsType, description: str):
        super().__init__(
            iri=iri,
            atoms_type=atoms_type,
            violation_type=ViolationType.MISSING,
            description=description,
            id=None,
        )


@dataclass
class InvalidFieldViolation(FieldViolationBase):
    """Represents a field that exists but is invalid."""

    def __init__(self, iri: str, atoms_type: AtomsType, description: str, id: Optional[UUID] = None):
        super().__init__(
            iri=iri,
            atoms_type=atoms_type,
            violation_type=ViolationType.INVALID,
            description=description,
            id=id,
        )


class ObjectStandardsGrade:
    def __init__(
        self,
        float_score: float,
        violations: list[FieldViolationBase],
        current_characteristics: int,
        total_characteristcs: int,
    ):
        self.float_score = float_score
        self.violations = violations
        self.ratio = f"{current_characteristics}/{total_characteristcs}"

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)


class ObjectStandardsRubric:
    def __init__(self):
        self.required_attrs: list[str] = []
        self.required_rels: list[str] = []

    @property
    def total_required_characteristics(self):
        return self.required_attrs + self.required_rels

    @property
    def total_required_characteristics_count(self):
        return len(self.total_required_characteristics)

    def grade(
        self,
        attributes: list[AttributesAttributesData] | None,
        relationships: list[RelationshipsRelationshipsData] | None,
    ) -> ObjectStandardsGrade:
        """
        Method to "grade" an object by calculating the fraction of required attributes and relationships it has
        """
        # Of the 'current' data on the node, get their IRIs to compare against the totatal required
        current_attrs: list[str] = []
        current_rels: list[str] = []
        if attributes:
            for attr in attributes:
                current_attrs.append(attr.attributeIri)

        if relationships:
            for rel in relationships:
                current_rels.append(rel.objectPropertyIri)

        current_characteristics_list = current_attrs + current_rels

        # not sure if get_current_count is needed considering the pipeline to this point
        # grabs attributes specified by IRI in the criteria already anyways
        current_characteristics_count = self.get_current_count(current_characteristics_list)
        float_score = self.get_float_score(current_characteristics_count)
        violations = self.get_missing_characteristics(current_attrs, current_rels)
        grade = ObjectStandardsGrade(
            float_score, violations, current_characteristics_count, self.total_required_characteristics_count
        )

        return grade

    def get_current_count(self, total_list: list[str]) -> int:
        return sum(1 for i in total_list if i in self.total_required_characteristics)

    def get_float_score(self, current_characteristics_count: int) -> float:
        return current_characteristics_count / self.total_required_characteristics_count

    def get_missing_characteristics(self, curr_attrs: list[str], curr_rels: list[str]) -> list[FieldViolationBase]:
        """
        Return a list of missing required characteristics as field violation objects.

        For missing fields, the Id will always be None as there is no ATOMS record to reference.
        """
        violations: list[FieldViolationBase] = []
        if self.required_attrs:
            for iri in self.required_attrs:
                if iri not in curr_attrs:
                    violations.append(
                        MissingFieldViolation(
                            iri=iri,
                            atoms_type=AtomsType.ATTRIBUTE,
                            description="Required attribute is missing.",
                        )
                    )
        if self.required_rels:
            for iri in self.required_rels:
                if iri not in curr_rels:
                    violations.append(
                        MissingFieldViolation(
                            iri=iri,
                            atoms_type=AtomsType.RELATIONSHIP,
                            description="Required relationship is missing.",
                        )
                    )

        return violations
