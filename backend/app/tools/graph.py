from sqlalchemy.orm import Session
from app.models import Entity, DocumentEntity, File

GET_ENTITY_GRAPH_TOOL = {
    "type": "function",
    "function": {
        "name": "get_entity_graph",
        "description": (
            "Look up an entity (concept, technology, person, organization, or topic) "
            "in the knowledge graph to find related documents and connected entities. "
            "Use this when you want to explore relationships between concepts in the workspace."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "description": "The name of the entity to look up (e.g. 'Python', 'FastAPI', 'John Smith')."
                }
            },
            "required": ["entity_name"]
        }
    }
}


def run_get_entity_graph(entity_name: str, workspace_id: str, db: Session) -> str:
    """
    Looks up an entity in the knowledge graph and returns:
    - Which documents mention it
    - What other entities appear in those same documents
    This lets the agent traverse the knowledge graph to find related concepts.
    """
    # Find the entity by name (case-insensitive) in this workspace
    entity = db.query(Entity).filter(
        Entity.workspace_id == workspace_id,
        Entity.name.ilike(f"%{entity_name}%")
    ).first()

    if not entity:
        return f"No entity named '{entity_name}' found in the knowledge graph for this workspace."

    # Find all documents that mention this entity
    doc_links = db.query(DocumentEntity).filter(
        DocumentEntity.entity_id == entity.id
    ).all()

    if not doc_links:
        return f"Entity '{entity.name}' exists but has no linked documents."

    file_ids = [link.file_id for link in doc_links]

    # For each document, find other entities mentioned in it (co-occurring entities)
    output_lines = [
        f"Entity: {entity.name} (type: {entity.entity_type})",
        f"Found in {len(file_ids)} document(s):\n"
    ]

    for file_id in file_ids:
        file = db.query(File).filter(File.id == file_id).first()
        filename = file.filename if file else str(file_id)

        # Get co-occurring entities in this document
        co_entity_links = db.query(DocumentEntity).filter(
            DocumentEntity.file_id == file_id,
            DocumentEntity.entity_id != entity.id
        ).limit(5).all()

        co_entity_ids = [l.entity_id for l in co_entity_links]
        co_entities = db.query(Entity).filter(Entity.id.in_(co_entity_ids)).all()
        co_names = [e.name for e in co_entities]

        output_lines.append(f"- Document: {filename}")
        if co_names:
            output_lines.append(f"  Related entities: {', '.join(co_names)}")

    return "\n".join(output_lines)