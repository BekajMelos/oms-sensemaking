from unittest.mock import MagicMock

import pytest

from src.oms_sensemaking.object_minimums.sensemaker import ObjectMinimumRubric


@pytest.fixture
def object_minimum_rubric():
    rubric = ObjectMinimumRubric()
    required_iris = ["iri1", "iri2", "relIri1"]
    rubric.required_iris = required_iris
    return rubric


def test_grade_with_all_required_elements_present(object_minimum_rubric):
    attributes_data = MagicMock(data=[MagicMock(attributeIri="iri1"), MagicMock(attributeIri="iri2")])
    relationships_data = MagicMock(data=[MagicMock(objectPropertyIri="relIri1")])

    grade_result = object_minimum_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 3 / len(object_minimum_rubric.required_iris)
    assert abs(grade_result.completion_score - expected_score) < 1e-9


def test_grade_with_some_required_elements_missing(object_minimum_rubric):
    attributes_data = MagicMock(data=[MagicMock(attributeIri="iri1")])
    relationships_data = MagicMock(data=[])

    grade_result = object_minimum_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 1 / len(object_minimum_rubric.required_iris)
    assert abs(grade_result.completion_score - expected_score) < 1e-9


def test_grade_with_no_required_elements_present(object_minimum_rubric):
    attributes_data = MagicMock(data=[])
    relationships_data = MagicMock(data=[])

    grade_result = object_minimum_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 0 / len(object_minimum_rubric.required_iris)
    assert abs(grade_result.completion_score - expected_score) < 1e-9
