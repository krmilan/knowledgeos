from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import WorkspaceMember, User
from app.schemas import ChatRequest, ChatResponse
from app.dependencies import get_current_user
from app.services.chat import chat_with_knowledge
import uuid

router = APIRouter(prefix="/workspaces/{workspace_id}/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
def chat(
    workspace_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify workspace membership
    membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == uuid.UUID(workspace_id),
        WorkspaceMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    result = chat_with_knowledge(
        question=payload.question,
        workspace_id=workspace_id
    )

    return result