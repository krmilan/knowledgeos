import asyncio
import time

from app.worker import celery_app
from app.database import SessionLocal
from app.models import File
from app.services.pdf import extract_text, chunk_text
from app.services.vector import store_chunks
from app.services.entity_extraction import extract_entities_from_chunk
from app.services.entity_resolution import resolve_entity, link_entity_to_document
import uuid
import logging

from app.websocket_manager import publish_to_workspace

logger = logging.getLogger(__name__)


def group_chunks_for_extraction(chunks: list[str], group_size: int = 1) -> list[str]:
    groups = []
    for i in range(0, len(chunks), group_size):
        group = " ".join(chunks[i:i + group_size])
        if group.strip():
            groups.append(group)
    return groups


@celery_app.task(name="process_file")
def process_file(file_id: str):
    db = SessionLocal()
    try:
        file = db.query(File).filter(
            File.id == uuid.UUID(file_id)
        ).first()

        if not file:
            return {"status": "error", "message": "File not found"}

        print(f"Processing file: {file.original_name}")

        if file.file_type == "pdf":
            text = extract_text(file.storage_path)
            print(f"Extracted {len(text)} characters")

            chunks = chunk_text(text)
            print(f"Created {len(chunks)} chunks")

            store_chunks(
                file_id=str(file.id),
                workspace_id=str(file.workspace_id),
                chunks=chunks
            )

            extraction_groups = group_chunks_for_extraction(chunks, group_size=1)
            print(f"Running entity extraction on {len(extraction_groups)} windows")

            for group in extraction_groups:
                try:
                    extracted = extract_entities_from_chunk(group)
                    for item in extracted:
                        entity = resolve_entity(
                            db,
                            workspace_id=file.workspace_id,
                            name=item["name"],
                            entity_type=item["type"],
                        )
                        link_entity_to_document(db, file_id=file.id, entity_id=entity.id)
                except Exception:
                    logger.exception("Entity extraction failed for a chunk of file %s", file_id)
                    continue
                time.sleep(2)  # avoid Groq free-tier rate limiting between chunks

        file.is_processed = True
        db.commit()

        asyncio.run(publish_to_workspace(str(file.workspace_id), {
            "type": "file_processed",
            "file_id": file_id,
            "file_name": file.original_name
        }))

        print(f"File {file.original_name} processed successfully")
        return {"status": "success", "file_id": file_id}

    except Exception as e:
        print(f"Error processing file: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()