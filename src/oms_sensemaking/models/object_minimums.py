"""Module for Object Minimum Sensemaker models"""

import json


class ObjectMinimumGrade:
    def __init__(self, score: float):
        self.completion_score = score

    def to_json(self) -> str:
        return json.dumps(self.__dict__)


class ObjectMinimumRubric:
    def __init__(self, required_iris: list[str]):
        self.required_iris = required_iris

    def grade(self, attributes: list[str]) -> ObjectMinimumGrade:
        """
        Method to "grade" an object by calculating the fraction of required attributes it has
        """
        count = sum(1 for attr in attributes if attr in self.required_iris)
        grade = ObjectMinimumGrade(count / len(self.required_iris))

        return grade
