from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, WorkspaceMember
from app.services.agent import run_research_agent

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str


@router.post("/workspaces/{workspace_id}/research")
def research(
    workspace_id: str,
    request: ResearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify user has access to this workspace
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = run_research_agent(
        query=request.query,
        workspace_id=workspace_id,
        db=db
    )

    return result