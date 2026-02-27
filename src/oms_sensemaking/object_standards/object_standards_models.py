"""Module for Object Standards Sensemaker models"""

import json
from typing import Any

from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributesData,
    RelationshipsRelationshipsData,
)
from pydantic import BaseModel, Field


class RequiredIris(BaseModel):
    """Required attribute and relationship IRIs for a rubric."""

    attribute_iris: list[str] = Field(default_factory=list)
    relationship_iris: list[str] = Field(default_factory=list)


class ObjectStandardsGrade:
    def __init__(
        self, float_score: float, violations: list[Any], current_characteristics: int, total_characteristcs: int
    ):
        self.float_score = float_score
        self.violations = violations
        self.ratio = f"{current_characteristics}/{total_characteristcs}"

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


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
        current_attrs = []
        current_rels = []
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
        # TODO apply what was said in in the comments of the .get_missing_characteristics(...) function definition
        grade = ObjectStandardsGrade(
            float_score, violations, current_characteristics_count, self.total_required_characteristics_count
        )

        return grade

    def get_current_count(self, total_list: list[str]) -> int:
        return sum(1 for i in total_list if i in self.total_required_characteristics)

    def get_float_score(self, current_characteristics_count: int) -> float:
        return current_characteristics_count / self.total_required_characteristics_count

    def get_missing_characteristics(self, curr_attrs: list[str], curr_rels: list[str]):
        # TODO this function will craft violation objects and return them in a list
        # when the schema is ready
        violations = []
        if self.required_attrs:
            for iri in self.required_attrs:
                if iri not in curr_attrs:
                    violations.append(iri)
        if self.required_rels:
            for iri in self.required_rels:
                if iri not in curr_rels:
                    violations.append(iri)

        return violations
