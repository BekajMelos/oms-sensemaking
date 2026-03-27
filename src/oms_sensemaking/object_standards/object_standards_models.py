"""Module for Object Standards Sensemaker models"""

import json

from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributesData,
    CompliantObjectInput,
    ObjectStandardsViolationInput,
    ObjectType,
    RelationshipsRelationshipsData,
    ViolationType,
)
from pydantic import BaseModel, Field


class RequiredIris(BaseModel):
    """Required attribute and relationship IRIs for a rubric."""

    attribute_iris: list[str] = Field(default_factory=list)
    relationship_iris: list[str] = Field(default_factory=list)


class ObjectStandardsGrade:
    def __init__(
        self,
        float_score: float,
        violations: list[ObjectStandardsViolationInput],
        current_characteristics: int,
        total_characteristcs: int,
        compliant_fields: list[CompliantObjectInput],
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
    def __init__(self) -> None:
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

    def get_missing_characteristics(
        self, curr_attrs: list[str], curr_rels: list[str]
    ) -> list[ObjectStandardsViolationInput]:
        """
        Return a list of missing required characteristics as Violation objects.

        For missing fields, atoms_id (id) is None as there is no ATOMS record to reference.
        """
        violations: list[ObjectStandardsViolationInput] = []
        if self.required_attrs:
            for iri in self.required_attrs:
                if iri not in curr_attrs:
                    violations.append(
                        ObjectStandardsViolationInput(
                            objectType=ObjectType.ATTRIBUTE,
                            iri=iri,
                            violationType=ViolationType.MISSING,
                            description=f"This object is missing a required attribute with IRI: {iri}.",
                        )
                    )
        if self.required_rels:
            for iri in self.required_rels:
                if iri not in curr_rels:
                    violations.append(
                        ObjectStandardsViolationInput(
                            objectType=ObjectType.RELATIONSHIP,
                            iri=iri,
                            violationType=ViolationType.MISSING,
                            description=(
                                f"This object is missing a required relationship with object property IRI: {iri}."
                            ),
                        )
                    )

        return violations

    def get_compliant_fields(
        self,
        atoms_attributes: list[AttributesAttributesData] | None,
        atoms_relationships: list[RelationshipsRelationshipsData] | None,
    ) -> list[CompliantObjectInput]:
        compliant_fields: list[CompliantObjectInput] = []
        if atoms_attributes:
            for attribute in atoms_attributes:
                compliant_fields.append(CompliantObjectInput(id=attribute.id, objectType=ObjectType.ATTRIBUTE))
        if atoms_relationships:
            for relationship in atoms_relationships:
                compliant_fields.append(CompliantObjectInput(id=relationship.id, objectType=ObjectType.RELATIONSHIP))
        return compliant_fields
