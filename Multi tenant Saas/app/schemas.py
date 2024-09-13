from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    org_name: str

class UserResponse(UserBase):
    id: int
    profile: Dict[str, Any]
    status: int
    settings: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirmRequest(BaseModel):
    token: str
    new_password: str

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str

class InviteMember(BaseModel):
    email: EmailStr
    org_id: int

class DeleteMember(BaseModel):
    member_id: int