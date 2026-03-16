from oms_sdk.generated.generated_graphql_client import (
    NodeNode,
    OntologyClassOntologyClass,
    OntologyRelationshipOntologyRelationship,
)
from pytest_mock import MockerFixture

from oms_sensemaking.clients.ontology_client import OntologyClient, OntologyService


class OntologyServiceHelper(OntologyService):
    pass


def test_ontology_service(mocker: MockerFixture):
    svc = OntologyServiceHelper()
    node = mocker.Mock(spec=NodeNode)

    # OntologyService is an Interface practically speaking
    # but is an Abstract Base Class, the methods are empty
    # so we can just call methods to satisfy code coverage

    svc.get_ontology_class("https://some/iri")
    svc.geospatial_get_node_ancestors_iris(node)
    svc.mil_symbol_get_node_ancestors_iris(node)
    svc.get_default_symbol_id_code("https://some/iri")
    svc.get_ontology_relationship("https://some/relationship/iri")


def test_geospatial_get_node_ancestors_iris_no_parent(mocker: MockerFixture, mock_oms_crud_tool):
    mock_ontology_class = mocker.Mock(spec=OntologyClassOntologyClass)
    mock_ontology_class.iri = "https://some/iri"
    mock_ontology_class.parentOntologyClasses = []

    mock_node = mocker.Mock(spec=NodeNode)
    mock_node.classIri = "https://some/iri"

    mocker.patch(
        "oms_sensemaking.clients.ontology_client.OntologyClient.get_ontology_class", return_value=mock_ontology_class
    )

    client = OntologyClient(mock_oms_crud_tool)

    actual_iris = client.geospatial_get_node_ancestors_iris(mock_node)
    assert actual_iris == set()


def _make_circular_ontology_setup(mocker: MockerFixture, mock_oms_crud_tool):
    """Build mocks for a circular ontology (A -> B -> A) and return client, mock_node, iri_a, iri_b."""
    iri_a = "https://some/iri/a"
    iri_b = "https://some/iri/b"

    mock_class_a = mocker.Mock(spec=OntologyClassOntologyClass)
    mock_class_a.iri = iri_a
    mock_class_a.defaultSymbolIdCode = None
    mock_parent_b = mocker.Mock()
    mock_parent_b.iri = iri_b
    mock_class_a.parentOntologyClasses = [mock_parent_b]

    mock_class_b = mocker.Mock(spec=OntologyClassOntologyClass)
    mock_class_b.iri = iri_b
    mock_class_b.defaultSymbolIdCode = None
    mock_parent_a = mocker.Mock()
    mock_parent_a.iri = iri_a
    mock_class_b.parentOntologyClasses = [mock_parent_a]

    def get_class(iri: str):
        if iri == iri_a:
            return mock_class_a
        if iri == iri_b:
            return mock_class_b
        return None

    mock_node = mocker.Mock(spec=NodeNode)
    mock_node.classIri = iri_a

    mocker.patch("oms_sensemaking.clients.ontology_client.OntologyClient.get_ontology_class", side_effect=get_class)
    client = OntologyClient(mock_oms_crud_tool)
    return client, mock_node, iri_a, iri_b


def test_geospatial_get_node_ancestors_iris_circular_reference(mocker: MockerFixture, mock_oms_crud_tool):
    """When ontology has circular class refs (A -> B -> A), return current set and stop."""
    client, mock_node, _, iri_b = _make_circular_ontology_setup(mocker, mock_oms_crud_tool)
    actual_iris = client.geospatial_get_node_ancestors_iris(mock_node)
    assert actual_iris == {iri_b}


def test_mil_symbol_get_node_ancestors_iris_circular_reference(mocker: MockerFixture, mock_oms_crud_tool):
    """When ontology has circular class ref (A -> B -> A), return current list and stop."""
    client, mock_node, _, iri_b = _make_circular_ontology_setup(mocker, mock_oms_crud_tool)
    actual_iris = client.mil_symbol_get_node_ancestors_iris(mock_node)
    assert actual_iris == [iri_b]


def test_get_default_symbol_id_code_circular_reference(mocker: MockerFixture, mock_oms_crud_tool):
    """When ontology has circular class ref (A -> B -> A), return None and stop."""
    client, _, iri_a, _ = _make_circular_ontology_setup(mocker, mock_oms_crud_tool)
    result = client.get_default_symbol_id_code(iri_a)
    assert result is None


def test_get_ontology_relationship(mocker: MockerFixture, mock_oms_crud_tool):
    mock_ontology_relationship = mocker.Mock(spec=OntologyRelationshipOntologyRelationship)
    mock_ontology_relationship.iri = "https://relationship/iri"
    mock_oms_crud_tool.get_ontology_relationship.return_value = mock_ontology_relationship

    svc = OntologyClient(mock_oms_crud_tool)

    actual = svc.get_ontology_relationship("https://relationship/iri")

    assert actual == mock_ontology_relationship, "Expected ontology relationship but got {}".format(actual)
    mock_oms_crud_tool.get_ontology_relationship.assert_called_once_with("https://relationship/iri")
