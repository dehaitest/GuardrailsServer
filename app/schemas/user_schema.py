# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr  
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    uuid: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenQuery(BaseModel):
    refresh_token: str

class UserWithToken(BaseModel):
    user: UserResponse
    token: Token