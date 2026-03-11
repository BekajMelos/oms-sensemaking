from unittest.mock import MagicMock

import pytest
from oms_sdk.generated.generated_graphql_client import ObjectType

from src.oms_sensemaking.object_standards.object_standards_models import (
    Violation,
    ViolationType,
)
from src.oms_sensemaking.object_standards.sensemaker import ObjectStandardsRubric


@pytest.fixture
def object_standards_rubric():
    rubric = ObjectStandardsRubric()
    required_attr_iris = ["iri1", "iri2"]
    required_rel_iris = ["relIri1"]
    rubric.required_attrs = required_attr_iris
    rubric.required_rels = required_rel_iris
    return rubric


def test_grade_with_all_required_elements_present(object_standards_rubric):
    attributes_data = [MagicMock(attributeIri="iri1"), MagicMock(attributeIri="iri2")]
    relationships_data = [MagicMock(objectPropertyIri="relIri1")]

    grade_result = object_standards_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 3 / len(object_standards_rubric.total_required_characteristics)
    assert abs(grade_result.float_score - expected_score) < 1e-9
    assert grade_result.ratio == "3/3"
    assert len(grade_result.violations) == 0
    assert len(grade_result.compliant_fields) == 3


def test_grade_with_some_required_elements_missing(object_standards_rubric):
    attributes_data = [MagicMock(attributeIri="iri1")]
    relationships_data = None

    grade_result = object_standards_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 1 / len(object_standards_rubric.total_required_characteristics)
    assert abs(grade_result.float_score - expected_score) < 1e-9
    assert grade_result.ratio == "1/3"
    assert len(grade_result.violations) == 2
    assert all(v.violation_type == ViolationType.MISSING for v in grade_result.violations)
    assert len(grade_result.compliant_fields) == 1


def test_grade_with_no_required_elements_present(object_standards_rubric):
    attributes_data = None
    relationships_data = None

    grade_result = object_standards_rubric.grade(attributes=attributes_data, relationships=relationships_data)

    expected_score = 0 / len(object_standards_rubric.total_required_characteristics)
    assert abs(grade_result.float_score - expected_score) < 1e-9
    assert grade_result.ratio == "0/3"
    assert len(grade_result.violations) == 3
    assert all(v.violation_type == ViolationType.MISSING for v in grade_result.violations)
    assert len(grade_result.compliant_fields) == 0


def test_get_current_count(object_standards_rubric):
    assert object_standards_rubric.get_current_count(["iri1"]) == 1


def test_get_float_score(object_standards_rubric):
    assert object_standards_rubric.get_float_score(len(["iri1", "relIri1"])) == (2 / 3)


def test_get_missing_characteristics(object_standards_rubric):
    missing_stuff = object_standards_rubric.get_missing_characteristics(["iri2"], [])
    iris = {v.iri for v in missing_stuff}
    assert "iri1" in iris
    assert "relIri1" in iris
    assert all(v.violation_type == ViolationType.MISSING for v in missing_stuff)


# --- Violation init tests ---


def test_violation_init_missing_attribute():
    """Violation with no characteristic (missing field): atoms_id is None."""
    v = Violation(
        object_type=ObjectType.ATTRIBUTE,
        iri="https://example.org/attr",
        violation_type=ViolationType.MISSING,
        description="Required attribute is missing.",
    )
    assert v.atoms_id is None
    assert v.atoms_type == ObjectType.ATTRIBUTE
    assert v.iri == "https://example.org/attr"
    assert v.violation_type == ViolationType.MISSING
    assert v.description == "Required attribute is missing."


def test_violation_init_missing_relationship():
    """Violation with no characteristic for missing relationship."""
    v = Violation(
        object_type=ObjectType.RELATIONSHIP,
        iri="https://example.org/rel",
        violation_type=ViolationType.MISSING,
        description="Required relationship is missing.",
    )
    assert v.atoms_id is None
    assert v.atoms_type == ObjectType.RELATIONSHIP
    assert v.iri == "https://example.org/rel"
    assert v.violation_type == ViolationType.MISSING
    assert v.description == "Required relationship is missing."


def test_violation_init_invalid_with_characteristic():
    """Violation with characteristic (invalid field): atoms_id comes from characteristic."""
    characteristic = MagicMock(id="attr-uuid-123")
    v = Violation(
        object_type=ObjectType.ATTRIBUTE,
        iri="https://example.org/attr",
        violation_type=ViolationType.INVALID,
        description="Attribute value is invalid.",
        characteristic=characteristic,
    )
    assert v.atoms_id == "attr-uuid-123"
    assert v.atoms_type == ObjectType.ATTRIBUTE
    assert v.iri == "https://example.org/attr"
    assert v.violation_type == ViolationType.INVALID
    assert v.description == "Attribute value is invalid."


def test_violation_init_invalid_relationship_with_characteristic():
    """Violation with relationship characteristic for invalid case."""
    characteristic = MagicMock(id="rel-uuid-456")
    v = Violation(
        object_type=ObjectType.RELATIONSHIP,
        iri="https://example.org/rel",
        violation_type=ViolationType.INVALID,
        description="Relationship target is invalid.",
        characteristic=characteristic,
    )
    assert v.atoms_id == "rel-uuid-456"
    assert v.atoms_type == ObjectType.RELATIONSHIP
    assert v.violation_type == ViolationType.INVALID
    assert v.description == "Relationship target is invalid."
