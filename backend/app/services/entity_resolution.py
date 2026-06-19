"""
backend/app/services/entity_resolution.py
"""

import re
import uuid
import logging

from sqlalchemy.orm import Session

from app.models import Entity, DocumentEntity
from app.services.vector import get_embedding, client, ENTITIES_COLLECTION

logger = logging.getLogger(__name__)

# Cosine similarity threshold: above this = same entity.
# 0.90 is conservative — tune after you have real data.
SIMILARITY_THRESHOLD = 0.90


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    name = name.strip().lower()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def resolve_entity(db: Session, workspace_id: uuid.UUID, name: str, entity_type: str) -> Entity:
    """
    Returns an existing Entity row if one matches (exact or near-duplicate),
    otherwise creates a new one and stores its embedding in Qdrant.
    """
    normalized = normalize_name(name)

    # Step 1: exact match (normalized) within this workspace + type
    candidates = (
        db.query(Entity)
        .filter(Entity.workspace_id == workspace_id, Entity.type == entity_type)
        .all()
    )
    for candidate in candidates:
        if normalize_name(candidate.name) == normalized:
            return candidate

    # Step 2: embed and similarity-search for near-duplicates
    embedding = get_embedding(name)

    results = client.query_points(
        collection_name=ENTITIES_COLLECTION,
        query=embedding,
        query_filter={
            "must": [
                {"key": "workspace_id", "match": {"value": str(workspace_id)}},
                {"key": "type", "match": {"value": entity_type}},
            ]
        },
        limit=1,
        score_threshold=SIMILARITY_THRESHOLD,
    ).points

    if results:
        matched_id = results[0].payload["entity_id"]
        matched = db.query(Entity).filter(Entity.id == matched_id).first()
        if matched:
            return matched

    # Step 3: no match — create new entity row + embedding point
    new_entity = Entity(workspace_id=workspace_id, name=name, type=entity_type)
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)

    client.upsert(
        collection_name=ENTITIES_COLLECTION,
        points=[
            {
                "id": new_entity.id,
                "vector": embedding,
                "payload": {
                    "entity_id": new_entity.id,
                    "workspace_id": str(workspace_id),
                    "type": entity_type,
                    "name": name,
                },
            }
        ],
    )
    return new_entity


def link_entity_to_document(db: Session, file_id: uuid.UUID, entity_id: int) -> DocumentEntity:
    """Idempotent: creates the (file_id, entity_id) link only if it doesn't exist."""
    existing = (
        db.query(DocumentEntity)
        .filter(DocumentEntity.file_id == file_id, DocumentEntity.entity_id == entity_id)
        .first()
    )
    if existing:
        return existing

    link = DocumentEntity(file_id=file_id, entity_id=entity_id)
    db.add(link)
    db.commit()
    return link