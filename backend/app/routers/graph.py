"""
backend/app/routers/graph.py
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Entity, DocumentEntity, File, WorkspaceMember


# --- Schemas ---

class EntityOut(BaseModel):
    id: int
    name: str
    type: str

    class Config:
        from_attributes = True


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # "document" | "entity"


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class RelatedDocument(BaseModel):
    file_id: str
    filename: str
    shared_entities: List[EntityOut]


class RelatedEntitiesResponse(BaseModel):
    entity: EntityOut
    related_documents: List[RelatedDocument]


# --- Router ---

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["graph"])


def _check_membership(db: Session, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    member = (
        db.query(WorkspaceMember)
        .filter_by(workspace_id=workspace_id, user_id=user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")


@router.get("/graph", response_model=GraphResponse)
def get_workspace_graph(
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_membership(db, workspace_id, current_user.id)

    links = (
        db.query(DocumentEntity, File, Entity)
        .join(File, DocumentEntity.file_id == File.id)
        .join(Entity, DocumentEntity.entity_id == Entity.id)
        .filter(Entity.workspace_id == workspace_id)
        .all()
    )

    nodes = {}
    edges = []
    for _, file, entity in links:
        doc_node_id = f"doc:{file.id}"
        entity_node_id = f"entity:{entity.id}"

        nodes.setdefault(doc_node_id, GraphNode(id=doc_node_id, label=file.original_name, node_type="document"))
        nodes.setdefault(entity_node_id, GraphNode(id=entity_node_id, label=entity.name, node_type="entity"))

        edges.append(GraphEdge(source=doc_node_id, target=entity_node_id))

    return GraphResponse(nodes=list(nodes.values()), edges=edges)


@router.get("/entities/{entity_id}/related", response_model=RelatedEntitiesResponse)
def get_related_documents(
    workspace_id: uuid.UUID,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_membership(db, workspace_id, current_user.id)

    entity = (
        db.query(Entity)
        .filter(Entity.id == entity_id, Entity.workspace_id == workspace_id)
        .first()
    )
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    doc_links = db.query(DocumentEntity).filter(DocumentEntity.entity_id == entity_id).all()

    related_documents = []
    for link in doc_links:
        file = db.query(File).filter(File.id == link.file_id).first()
        if not file:
            continue

        shared_entities = (
            db.query(Entity)
            .join(DocumentEntity, DocumentEntity.entity_id == Entity.id)
            .filter(DocumentEntity.file_id == file.id)
            .all()
        )

        related_documents.append(
            RelatedDocument(
                file_id=str(file.id),
                filename=file.original_name,
                shared_entities=[EntityOut.model_validate(e) for e in shared_entities],
            )
        )

    return RelatedEntitiesResponse(
        entity=EntityOut.model_validate(entity),
        related_documents=related_documents,
    )