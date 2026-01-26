"""Module for Object Minimum Sensemaker models"""

import json
from typing import Any

from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributes,
    RelationshipsRelationships,
)


class ObjectMinimumGrade:
    def __init__(
        self, float_score: float, violations: list[Any], current_characteristics: int, total_characteristcs: int
    ):
        self.float_score = float_score
        self.violations = violations
        self.ratio = f"{current_characteristics}/{total_characteristcs}"

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


class ObjectMinimumRubric:
    def __init__(self):
        self.required_attrs: None | list[str] = None
        self.required_rels: None | list[str] = None

    @property
    def total_required_characteristics(self):
        return self.required_attrs + self.required_rels

    @property
    def total_required_characteristics_count(self):
        return len(self.total_required_characteristics)

    def grade(
        self, attributes: AttributesAttributes | None, relationships: RelationshipsRelationships | None
    ) -> ObjectMinimumGrade:
        """
        Method to "grade" an object by calculating the fraction of required attributes and relationships it has
        """
        # Of the 'current' data on the node, get their IRIs to compare against the totatal required
        current_attr_iris = []
        current_relationship_iris = []
        if attributes:
            for attr in attributes.data:
                current_attr_iris.append(attr.attributeIri)

        if relationships:
            for rel in relationships.data:
                current_relationship_iris.append(rel.objectPropertyIri)

        current_characteristics_list = current_attr_iris + current_relationship_iris

        # not sure if get_current_count is needed considering the pipeline to this point
        # grabs attributes specified by IRI in the criteria already anyways
        current_characteristics_count = self.get_current_count(current_characteristics_list)
        float_score = self.get_float_score(current_characteristics_count)
        violations = self.get_missing_characteristics(current_attr_iris, current_relationship_iris)
        # TODO apply what was said in in the comments of the .get_missing_characteristics(...) function definition
        grade = ObjectMinimumGrade(
            float_score, violations, current_characteristics_count, self.total_required_characteristics_count
        )

        return grade

    def get_current_count(self, total_list: list[str]) -> int:
        return sum(1 for i in total_list if i in self.total_required_characteristics)

    def get_float_score(self, current_characteristics_count: int) -> float:
        return current_characteristics_count / self.total_required_characteristics_count

    def get_missing_characteristics(self, curr_attr_iris: list[str], curr_rel_iris: list[str]):
        # TODO this function will craft violation objects and return them in a list
        # when the schema is ready
        violations = []
        for iri in self.required_attrs:
            if iri not in curr_attr_iris:
                violations.append(iri)
        for iri in self.required_rels:
            if iri not in curr_rel_iris:
                violations.append(iri)

        return violations
