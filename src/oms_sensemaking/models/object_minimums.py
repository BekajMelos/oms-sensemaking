"""Module for Object Minimum Sensemaker models"""

import json

from oms_sdk.generated.generated_graphql_client import (
    AttributesAttributes,
    RelationshipsRelationships,
)


class ObjectMinimumGrade:
    def __init__(self, score: float):
        self.completion_score = score

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


class ObjectMinimumRubric:
    def __init__(self, required_iris: list[str]):
        self.required_iris = required_iris

    def grade(self, attributes: AttributesAttributes, relationships: RelationshipsRelationships) -> ObjectMinimumGrade:
        """
        Method to "grade" an object by calculating the fraction of required attributes and relationships it has
        """
        attr_iris = []
        relationship_iris = []
        for attr in attributes.data:
            attr_iris.append(attr.attributeIri)
        for rel in relationships.data:
            relationship_iris.append(rel.objectPropertyIri)

        total_list = attr_iris + relationship_iris
        count = sum(1 for i in total_list if i in self.required_iris)
        grade = ObjectMinimumGrade(count / len(self.required_iris))

        return grade
