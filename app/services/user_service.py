# app/services/user_service.py
from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from ..models.user_model import User
from ..core.security import hash_password
from ..core.config import settings
from ..common import id_generation
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.config import settings
from app.core.security import verify_password

# Create user
async def create_user(db: AsyncSession, user_data: dict) -> User:
    hashed_password = hash_password(user_data.pop('password'))
    uuid = 'user_{}'.format(id_generation.generate_id())
    while await get_user_by_uuid(db, uuid):
        uuid = 'user_{}'.format(id_generation.generate_id())
    db_user = User(**user_data, uuid=uuid, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

# Edit user by UUID
async def edit_user_by_uuid(db: AsyncSession, user_uuid: str, update_data: dict) -> User:
    query = select(User).where(User.uuid == user_uuid)
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()
    if db_user is not None:
        update_other_than_last_login = any(key != "last_login" for key in update_data.keys())
        for key, value in update_data.items():
            setattr(db_user, key, value)
        if update_other_than_last_login:
            db_user.update_datetime = datetime.utcnow()
        await db.commit()
        await db.refresh(db_user)
        return db_user
    return None

# Get user by Email
async def get_user_by_email(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

# Delete user by Email
async def delete_user_by_email(db: AsyncSession, email: str) -> None:
    result = await db.execute(delete(User).where(User.email == email))
    await db.commit()
    return result.rowcount > 0

# Get user by UUID
async def get_user_by_uuid(db: AsyncSession, uuid: str) -> User:
    result = await db.execute(select(User).where(User.uuid == uuid))
    return result.scalar_one_or_none()

# Authenticate user
async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token(data: dict) -> str:
    return create_token(data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(data: dict) -> str:
    return create_token(data, timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))

async def validate_token(db: AsyncSession, token: str) -> Union[str, bool]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        uuid = payload.get("sub")
        expiry = payload.get("exp")
        if uuid is None or expiry is None or datetime.fromtimestamp(expiry, timezone.utc) < datetime.now(timezone.utc):
            return False
        user = await get_user_by_uuid(db, uuid)
        return uuid if user else False
    except JWTError:
        return False
