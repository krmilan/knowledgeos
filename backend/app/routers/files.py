from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import File as FileModel, WorkspaceMember, User
from app.schemas import FileResponse
from app.dependencies import get_current_user
from app.services.storage import save_file
from app.tasks import process_file
from typing import List
import uuid
import os
from app.models import Entity, DocumentEntity
from app.services.vector import delete_chunks_by_file

router = APIRouter(prefix="/workspaces/{workspace_id}/files", tags=["Files"])

def get_workspace_or_404(workspace_id: str, user: User, db: Session):
    membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == uuid.UUID(workspace_id),
        WorkspaceMember.user_id == user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    return membership.workspace

@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    workspace_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = get_workspace_or_404(workspace_id, current_user, db)

    try:
        file_data = await save_file(file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    db_file = FileModel(
        workspace_id=workspace.id,
        uploaded_by=current_user.id,
        **file_data
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Trigger background processing
    process_file.delay(str(db_file.id))

    return db_file

@router.get("/", response_model=List[FileResponse])
def list_files(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = get_workspace_or_404(workspace_id, current_user, db)

    files = db.query(FileModel).filter(
        FileModel.workspace_id == workspace.id
    ).all()

    return files

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    workspace_id: str,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = get_workspace_or_404(workspace_id, current_user, db)

    db_file = db.query(FileModel).filter(
        FileModel.id == uuid.UUID(file_id),
        FileModel.workspace_id == workspace.id
    ).first()

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # 1. Remove vector chunks from Qdrant
    delete_chunks_by_file(file_id)

    # 2. Find entities that are ONLY linked to this file — they'll be orphaned
    candidate_entity_ids = [
        row.entity_id for row in
        db.query(DocumentEntity).filter(DocumentEntity.file_id == db_file.id).all()
    ]

    # 3. Delete the PDF from disk
    if db_file.storage_path and os.path.exists(db_file.storage_path):
        os.remove(db_file.storage_path)

    # 4. Delete the File row — cascades to DocumentEntity rows automatically
    db.delete(db_file)
    db.flush()  # apply the cascade delete before checking orphans

    # 5. Clean up entities that now have zero document links
    for entity_id in candidate_entity_ids:
        remaining_links = db.query(DocumentEntity).filter(
            DocumentEntity.entity_id == entity_id
        ).count()
        if remaining_links == 0:
            orphaned_entity = db.query(Entity).filter(Entity.id == entity_id).first()
            if orphaned_entity:
                db.delete(orphaned_entity)

    db.commit()
    return None