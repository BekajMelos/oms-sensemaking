from oms_sdk.generated.generated_graphql_client import NodeNode, OntologyClassOntologyClass
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
