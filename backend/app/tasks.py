from app.worker import celery_app
from app.database import SessionLocal
from app.models import File
from app.services.pdf import extract_text, chunk_text
from app.services.vector import store_chunks
import uuid

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
            # Extract text
            text = extract_text(file.storage_path)
            print(f"Extracted {len(text)} characters")

            # Chunk text
            chunks = chunk_text(text)
            print(f"Created {len(chunks)} chunks")

            # Store in Qdrant
            store_chunks(
                file_id=str(file.id),
                workspace_id=str(file.workspace_id),
                chunks=chunks
            )

        # Mark as processed
        file.is_processed = True
        db.commit()

        print(f"File {file.original_name} processed successfully")
        return {"status": "success", "file_id": file_id}

    except Exception as e:
        print(f"Error processing file: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()