"""The semantic module contains endpoints that return information about the service."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from oms_sensemaking.api.schemas.oms import Attribute, CreateObjectResponse, DeleteObjectResponse, Node, Relationship
from oms_sensemaking.clients import get_db_session
from oms_sensemaking.models.semantic import Node as OrmNode

router: APIRouter = APIRouter()


@router.post("/attribute", response_model=CreateObjectResponse, response_model_exclude_none=True)
def create_attribute(db: Annotated[Session, Depends(get_db_session)], attribute: Attribute) -> CreateObjectResponse:
    """Create an attribute in the graph."""
    return CreateObjectResponse(success=True)


@router.delete("/attribute/{attribute_id}", response_model=DeleteObjectResponse, response_model_exclude_none=True)
def delete_attribute(db: Annotated[Session, Depends(get_db_session)], attribute_id: str) -> DeleteObjectResponse:
    """Delete an attribute in the graph."""
    return DeleteObjectResponse(success=True)

@router.get("/node", response_model=list[Node])
def get_nodes(db: Annotated[Session, Depends(get_db_session)]):
    """Gets all nodes in the graph."""
    nodes = db.query(OrmNode).all()
    return nodes

@router.post("/node", response_model=CreateObjectResponse, response_model_exclude_none=True)
def create_node(db: Annotated[Session, Depends(get_db_session)], node: Node) -> CreateObjectResponse:
    """Create a node in the graph."""
    orm_node = OrmNode(**node.model_dump())
    db.add(orm_node)
    db.commit()
    db.refresh(orm_node)
    return CreateObjectResponse(success=True)


@router.delete("/node/{node_id}", response_model=DeleteObjectResponse, response_model_exclude_none=True)
def delete_node(db: Annotated[Session, Depends(get_db_session)], node_id: str) -> DeleteObjectResponse:
    """Delete a node in the graph."""
    return DeleteObjectResponse(success=True)


@router.post("/relationship", response_model=CreateObjectResponse, response_model_exclude_none=True)
def create_relationship(
        db: Annotated[Session, Depends(get_db_session)],
        relationship: Relationship) -> CreateObjectResponse:
    """Create a relationship in the graph."""
    return CreateObjectResponse(success=True)


@router.delete("/relationship/{relationship_id}",
               response_model=DeleteObjectResponse,
               response_model_exclude_none=True)
def delete_relationship(
        db: Annotated[Session, Depends(get_db_session)],
        relationship_id: str) -> DeleteObjectResponse:
    """Delete a relationship in the graph."""
    return DeleteObjectResponse(success=True)
