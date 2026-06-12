from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Workspace, WorkspaceMember, WorkspaceRole, User
from app.schemas import WorkspaceCreate, WorkspaceResponse
from app.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create workspace
    workspace = Workspace(
        name=payload.name,
        description=payload.description
    )
    db.add(workspace)
    db.flush()  # Get the ID without committing

    # Add creator as owner
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=WorkspaceRole.owner
    )
    db.add(membership)
    db.commit()
    db.refresh(workspace)

    return workspace

@router.get("/", response_model=List[WorkspaceResponse])
def get_my_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    memberships = db.query(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id
    ).all()

    return [m.workspace for m in memberships]