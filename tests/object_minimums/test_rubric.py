from unittest.mock import MagicMock

import pytest

from src.oms_sensemaking.object_minimums.sensemaker import ObjectMinimumRubric


@pytest.fixture
def object_minimum_rubric():
    rubric = ObjectMinimumRubric()
    required_attr_iris = ["iri1", "iri2"]
    required_rel_iris = ["relIri1"]
    rubric.required_attrs = required_attr_iris
    rubric.required_rels = required_rel_iris
    return rubric


def test_grade_with_all_required_elements_present(object_minimum_rubric):
    attributes_data = MagicMock(data=[MagicMock(attributeIri="iri1"), MagicMock(attributeIri="iri2")])
    relationships_data = MagicMock(data=[MagicMock(objectPropertyIri="relIri1")])

    grade_result = object_minimum_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 3 / len(object_minimum_rubric.total_required_characteristics)
    assert abs(grade_result.float_score - expected_score) < 1e-9
    assert grade_result.ratio == "3/3"
    assert len(grade_result.violations) == 0


def test_grade_with_some_required_elements_missing(object_minimum_rubric):
    attributes_data = MagicMock(data=[MagicMock(attributeIri="iri1")])
    relationships_data = MagicMock(data=[])

    grade_result = object_minimum_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 1 / len(object_minimum_rubric.total_required_characteristics)
    assert abs(grade_result.float_score - expected_score) < 1e-9
    assert grade_result.ratio == "1/3"
    assert len(grade_result.violations) == 2


def test_grade_with_no_required_elements_present(object_minimum_rubric):
    attributes_data = MagicMock(data=[])
    relationships_data = MagicMock(data=[])

    grade_result = object_minimum_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 0 / len(object_minimum_rubric.total_required_characteristics)
    assert abs(grade_result.float_score - expected_score) < 1e-9
    assert grade_result.ratio == "0/3"
    assert len(grade_result.violations) == 3


def test_get_current_count(object_minimum_rubric):
    assert object_minimum_rubric.get_current_count(["iri1"]) == 1


def test_get_float_score(object_minimum_rubric):
    assert object_minimum_rubric.get_float_score(len(["iri1", "relIri1"])) == (2 / 3)


def test_get_missing_characteristics(object_minimum_rubric):
    # this test is due to change with coming schema changes
    missing_stuff = object_minimum_rubric.get_missing_characteristics(["iri2"], [])
    assert "iri1" in missing_stuff
    assert "relIri1" in missing_stuff
