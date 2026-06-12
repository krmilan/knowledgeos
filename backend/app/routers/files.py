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