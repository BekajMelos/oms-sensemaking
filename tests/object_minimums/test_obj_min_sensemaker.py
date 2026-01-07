import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from oms_sdk.generated.generated_graphql_client import AttributeAttribute

from oms_sensemaking.core.oms_crud import OmsCrudTool
from src.oms_sensemaking.object_minimums.sensemaker import (
    ObjectMinimumDataRetriever,
    ObjectMinimumRubric,
    ObjectMinimums,
)


class TestObjectMinimumSensemaker(unittest.TestCase):
    def setUp(self):
        self.mock_oms_crud_tool = MagicMock(spec=OmsCrudTool)
        self.mock_retriever = MagicMock(spec=ObjectMinimumDataRetriever)
        self.mock_rubric = MagicMock()
        rubric_criteria = {}

        self.sensemaker = ObjectMinimums(
            oms_crud_tool=self.mock_oms_crud_tool,
            obj_min_retriever=self.mock_retriever,
            obj_min_rubric=self.mock_rubric,
            rubric_criteria=rubric_criteria,
        )

    def test_process_data_no_required_iris(self):
        attribute_of_node = MagicMock(spec=AttributeAttribute)
        attribute_of_node.nodeId = str(uuid4())

        # Mock the node and its class IRI
        mock_node = MagicMock()
        mock_node.classIri = "http://example.org/ClassIRI"
        self.mock_oms_crud_tool.get_node.return_value = mock_node

        # Mock config to return no required IRIs
        self.sensemaker._get_required_iris = MagicMock(return_value=([], []))

        result = self.sensemaker.process_data(attribute_of_node)

        self.mock_retriever.retrieve_data_for_grading.assert_not_called()
        self.assertEqual(result, [])

    def test_process_data_with_attributes_and_relationships(self):
        attribute_of_node = MagicMock(spec=AttributeAttribute)
        attribute_of_node.nodeId = str(uuid4())

        # Mock the node and its class IRI
        mock_node = MagicMock()
        mock_node.classIri = "http://example.org/ClassIRI"
        self.mock_oms_crud_tool.get_node.return_value = mock_node

        required_attributes = ["iri1", "iri2"]
        required_relationships = ["relIri1", "relIri2"]

        # Mock config to return some required IRIs
        self.sensemaker._get_required_iris = MagicMock(return_value=(required_attributes, required_relationships))

        # Mock retrieval of attributes and relationships
        mock_attributes = [{"attribute": "value"}]
        mock_relationships = [{"relationship": "value"}]

        self.mock_retriever.retrieve_data_for_grading.return_value = {
            "attributes": mock_attributes,
            "relationships": mock_relationships,
        }

        # Mock grading calculation
        mock_grade = MagicMock()
        self.sensemaker._calculate_grade = MagicMock(return_value=mock_grade)

        result = self.sensemaker.process_data(attribute_of_node)

        self.mock_retriever.retrieve_data_for_grading.assert_called_once_with(
            self.mock_oms_crud_tool, mock_node, required_attributes, required_relationships
        )
        self.assertEqual(result, [])

    @patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_node")
    def test_get_required_iris(self, mock_get_node):
        class_iri = "http://example.org/ClassIRI"
        config_rubrics = {class_iri: {"ATTRIBUTES": ["iri1", "iri2"], "RELATIONSHIPS": ["relIri1"]}}

        self.sensemaker.config_rubrics = config_rubrics
        required_attributes, required_relationships = self.sensemaker._get_required_iris(class_iri)

        self.assertEqual(required_attributes, ["iri1", "iri2"])
        self.assertEqual(required_relationships, ["relIri1"])

    @patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_node")
    def test_calculate_grade(self, mock_get_node):
        attributes = [{"attribute": "value"}]
        relationships = [{"relationship": "value"}]

        self.sensemaker._calculate_grade(attributes, relationships)

        self.mock_rubric.grade.assert_called_once_with(attributes=attributes, relationships=relationships)


class TestObjectMinimumRubric(unittest.TestCase):
    def setUp(self):
        self.rubric = ObjectMinimumRubric()
        self.required_iris = ["iri1", "iri2", "relIri1"]
        self.rubric.required_iris = self.required_iris

    def test_grade_with_all_required_elements_present(self):
        # Mock data where all required IRIs are present
        attributes_data = MagicMock(data=[MagicMock(attributeIri="iri1"), MagicMock(attributeIri="iri2")])
        relationships_data = MagicMock(data=[MagicMock(objectPropertyIri="relIri1")])

        grade_result = self.rubric.grade(attributes=attributes_data, relationships=relationships_data)

        # All required IRIs are present
        expected_score = 3 / len(self.required_iris)
        self.assertAlmostEqual(grade_result.completion_score, expected_score)

    def test_grade_with_some_required_elements_missing(self):
        # Mock data where some required IRIs are missing
        attributes_data = MagicMock(data=[MagicMock(attributeIri="iri1")])
        relationships_data = MagicMock(data=[])

        grade_result = self.rubric.grade(attributes=attributes_data, relationships=relationships_data)

        # Only one of the three required IRIs is present
        expected_score = 1 / len(self.required_iris)
        self.assertAlmostEqual(grade_result.completion_score, expected_score)

    def test_grade_with_no_required_elements_present(self):
        # Mock data where none of the required IRIs are present
        attributes_data = MagicMock(data=[])
        relationships_data = MagicMock(data=[])

        grade_result = self.rubric.grade(attributes=attributes_data, relationships=relationships_data)

        # None of the required IRIs is present
        expected_score = 0 / len(self.required_iris)
        self.assertAlmostEqual(grade_result.completion_score, expected_score)
