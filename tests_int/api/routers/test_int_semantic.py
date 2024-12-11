from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from httpx import Response
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.api.schemas.oms import CreateObjectResponse, DeleteObjectResponse, Node


def test_create_node(client: TestClient, db: Session):
    create_node(client)


def test_delete_node(client: TestClient, db: Session):
    # create the node
    node_id: UUID = create_node(client)

    # delete the node
    response = client.delete(f"/semantic/node/{node_id}")
    assert response.status_code == 200
    assert DeleteObjectResponse(**response.json()).success


def create_node(client: TestClient) -> UUID:
    """
    Create and validate a Node.

    :param client: A ReST test client for FastAPI.
    :return: The node ID.
    """
    node_id: UUID = uuid4()

    response: Response = client.post(
        "/semantic/node",
        json=Node(
            id=node_id,
            version=1,
            acm=DEFAULT_ACM,
            tags=["tag1", "tag2"],
            guide_id="guideID",
            name="TestNode",
            tier="PRIMARY",
            class_iri="http://purl.obolibrary.org/obo/BFO_0000030",
            class_name="Object",
            ifc_codes=["ifcCode1", "ifcCode2"],
            allegiance="allegiance",
            allegiance_aor="allegianceAor",
            current_aor="currentAor",
            is_nso=True,
        ).model_dump(),
    )
    assert response.status_code == 200
    assert CreateObjectResponse(**response.json()).success

    return node_id
