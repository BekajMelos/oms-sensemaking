"""Tests for the "semantic" API."""
from typing import Optional
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from httpx import Response
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.api.schemas.oms import Attribute, CreateObjectResponse, DeleteObjectResponse, Node, Relationship


def test_create_attribute(client: TestClient):
    create_attribute(client)


def test_delete_attribute(client: TestClient):
    # create the attribute
    attribute_id: UUID = create_attribute(client)

    # delete the attribute
    response = client.delete(f"/semantic/attribute/{attribute_id}")
    assert response.status_code == 200
    assert DeleteObjectResponse(**response.json()).success


def test_create_node(client: TestClient):
    create_node(client)


def test_delete_node(client: TestClient):
    # create the node
    node_id: UUID = create_node(client)

    # delete the node
    response = client.delete(f"/semantic/node/{node_id}")
    assert response.status_code == 200
    assert DeleteObjectResponse(**response.json()).success


def test_create_relationship(client: TestClient):
    create_relationship(client)


def test_delete_relationship(client: TestClient):
    # create the relationship
    relationship_id: UUID = create_relationship(
        client,
        UUID("63a17206-8d4d-4825-9b0e-958cf54fa639"),
        UUID("4d93fac7-5659-4ca9-b735-84aad702cee0")
    )

    # delete the relationship
    response = client.delete(f"/semantic/relationship/{relationship_id}")
    assert response.status_code == 200
    assert DeleteObjectResponse(**response.json()).success


def create_attribute(client: TestClient) -> UUID:
    """
    Create and validate an Attribute.

    :param client: A ReST test client for FastAPI.
    :return: The attribute ID.
    """
    attribute_id: UUID = uuid4()

    # create an attribute
    response: Response = client.post(
        "/semantic/attribute",
        json=Attribute(
            id=attribute_id,
            version=1,
            acm=DEFAULT_ACM,
            attribute_iri="https://foundry.ai.mil/DICO/v3.1.0/Common_Name",
            attribute_name="Common Name",
            attribute_value="test value"
        ).model_dump()
    )
    assert response.status_code == 200
    assert CreateObjectResponse(**response.json()).success

    return attribute_id


def create_node(client: TestClient) -> UUID:
    """
    Create and validate a Node.

    :param client: A ReST test client for FastAPI.
    :return: The node ID.
    """
    node_id: UUID = uuid4()

    response: Response = client.post(
        '/semantic/node',
        json=Node(
            id=node_id,
            version=1,
            acm=DEFAULT_ACM,
            name="TestNode",
            class_iri="http://purl.obolibrary.org/obo/BFO_0000030",
            class_name="Object"
        ).model_dump()
    )
    assert response.status_code == 200
    assert CreateObjectResponse(**response.json()).success

    return node_id


def create_relationship(
        client: TestClient,
        start_node_id: Optional[UUID] = None,
        end_node_id: Optional[UUID] = None) -> UUID:
    """
    Create and validate a Relationship.

    :param client: A ReST test client for FastAPI.
    :param start_node_id: The UUID of the start node.
    :param end_node_id: The UUID of the end node.
    :return: The relationship ID.
    """
    relationship_id: UUID = uuid4()

    if start_node_id is None:
        start_node_id = uuid4()

    if end_node_id is None:
        end_node_id = uuid4()

    response: Response = client.post(
        "/semantic/relationship",
        json=Relationship(
            id=relationship_id,
            version=1,
            acm=DEFAULT_ACM,
            name="foo",
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            object_property_iri="http://schema.dia.mil/DefenseIntelligenceCoreOntology/objectCreator",
            object_property_name="Object Creator"
        ).model_dump()
    )
    assert response.status_code == 200
    assert CreateObjectResponse(**response.json()).success

    return relationship_id
