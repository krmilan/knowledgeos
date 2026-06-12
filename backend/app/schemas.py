from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

# --- Request Schemas (data coming IN) ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 72:
            raise ValueError("Password cannot exceed 72 characters")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Response Schemas (data going OUT) ---

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    
class WorkspaceRoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"

# --- Workspace Schemas ---

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class WorkspaceMemberResponse(BaseModel):
    user: UserResponse
    role: WorkspaceRoleEnum
    joined_at: datetime

    class Config:
        from_attributes = True