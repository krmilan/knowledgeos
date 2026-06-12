from app.worker import celery_app
from app.database import SessionLocal
from app.models import File
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

        # Phase 6 will add real processing here:
        # 1. Extract text from PDF
        # 2. Chunk the text
        # 3. Generate embeddings
        # 4. Store in Qdrant

        # For now just mark as processed
        file.is_processed = True
        db.commit()

        print(f"File {file.original_name} processed successfully")
        return {"status": "success", "file_id": file_id}

    except Exception as e:
        print(f"Error processing file: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()