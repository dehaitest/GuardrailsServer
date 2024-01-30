# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Tuple, List

class UserCreate(BaseModel):
    name: str
    email: EmailStr  
    password: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    active: Optional[bool] = None

class UserResponse(BaseModel):
    uuid: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    active: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenQuery(BaseModel):
    refresh_token: str

class UserWithToken(BaseModel):
    user: UserResponse
    token: Token

class SetupUserQuery(BaseModel):
    user_id: str
    resolution: Tuple[int, int]
    app_list: List[str]