"""Module for Object Standards Sensemaker models"""

import enum
import json

from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributesData,
    ObjectType,
    RelationshipsRelationshipsData,
)
from pydantic import BaseModel, Field


class ObjectStandardsCharacteristic:
    def __init__(
        self, characteristic: AttributesAttributesData | RelationshipsRelationshipsData | None, object_type: ObjectType
    ):
        self.atoms_id = characteristic.id if characteristic else None
        self.atoms_type = object_type


class CompliantField(ObjectStandardsCharacteristic):
    def __init__(
        self, characteristic: AttributesAttributesData | RelationshipsRelationshipsData, object_type: ObjectType
    ):
        super().__init__(characteristic, object_type)

    def __str__(self) -> str:
        return str(self.atoms_id)


class ViolationType(str, enum.Enum):
    """Type of Object Standards field violation."""

    MISSING = "MISSING"
    INVALID = "INVALID"


class Violation(ObjectStandardsCharacteristic):
    """
    Object Standards field violation (missing or invalid).

    Id (atoms_id) is the ATOMS identifier for the field when it exists;
    for missing fields this is None.
    """

    def __init__(
        self,
        object_type: ObjectType,
        iri: str,
        violation_type: ViolationType,
        description: str,
        characteristic: AttributesAttributesData | RelationshipsRelationshipsData | None = None,
    ):
        super().__init__(characteristic, object_type)
        self.iri = iri
        self.violation_type = violation_type
        self.description = description

    def __str__(self) -> str:
        return f"{self.violation_type.value} {self.atoms_type.value}: {self.iri}"


class RequiredIris(BaseModel):
    """Required attribute and relationship IRIs for a rubric."""

    attribute_iris: list[str] = Field(default_factory=list)
    relationship_iris: list[str] = Field(default_factory=list)


class ObjectStandardsGrade:
    def __init__(
        self,
        float_score: float,
        violations: list[Violation],
        current_characteristics: int,
        total_characteristcs: int,
        compliant_fields: list[CompliantField],
    ):
        self.float_score = float_score
        self.violations = violations
        self.ratio = f"{current_characteristics}/{total_characteristcs}"
        self.compliant_fields = compliant_fields

    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

    def __str__(self) -> str:
        return f"float_score={self.float_score}, ratio={self.ratio}"


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
        compliant_fields = self.get_compliant_fields(attributes, relationships)
        # TODO apply what was said in in the comments of the .get_missing_characteristics(...) function definition
        grade = ObjectStandardsGrade(
            float_score,
            violations,
            current_characteristics_count,
            self.total_required_characteristics_count,
            compliant_fields,
        )

        return grade

    def get_current_count(self, total_list: list[str]) -> int:
        return sum(1 for i in total_list if i in self.total_required_characteristics)

    def get_float_score(self, current_characteristics_count: int) -> float:
        return current_characteristics_count / self.total_required_characteristics_count

    def get_missing_characteristics(self, curr_attrs: list[str], curr_rels: list[str]) -> list[Violation]:
        """
        Return a list of missing required characteristics as Violation objects.

        For missing fields, atoms_id (id) is None as there is no ATOMS record to reference.
        """
        violations: list[Violation] = []
        if self.required_attrs:
            for iri in self.required_attrs:
                if iri not in curr_attrs:
                    violations.append(
                        Violation(
                            object_type=ObjectType.ATTRIBUTE,
                            iri=iri,
                            violation_type=ViolationType.MISSING,
                            description="Required attribute is missing.",
                        )
                    )
        if self.required_rels:
            for iri in self.required_rels:
                if iri not in curr_rels:
                    violations.append(
                        Violation(
                            object_type=ObjectType.RELATIONSHIP,
                            iri=iri,
                            violation_type=ViolationType.MISSING,
                            description="Required relationship is missing.",
                        )
                    )

        return violations

    def get_compliant_fields(
        self,
        atoms_attributes: list[AttributesAttributesData] | None,
        atoms_relationships: list[RelationshipsRelationshipsData] | None,
    ) -> list[CompliantField]:
        compliant_fields: list[CompliantField] = []
        if atoms_attributes:
            for attribute in atoms_attributes:
                compliant_fields.append(CompliantField(attribute, ObjectType.ATTRIBUTE.value))
        if atoms_relationships:
            for relationship in atoms_relationships:
                compliant_fields.append(CompliantField(relationship, ObjectType.RELATIONSHIP.value))
        return compliant_fields
