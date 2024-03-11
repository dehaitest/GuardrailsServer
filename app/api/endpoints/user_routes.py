# app/api/v1/endpoints/user_routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from ...services import user_service
from ...services.database import get_db_session
from ...schemas.user_schema import UserCreate, UserResponse, UserWithToken, Token, UserUpdate, RefreshTokenQuery
from fastapi.responses import JSONResponse
from ..dependencies import get_current_user

router = APIRouter()

# Create user / Sign up
@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    if await user_service.get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email address is already in use."
        )
    return await user_service.create_user(db, user.model_dump())

# Get user by UUID
@router.get("/users/by-uuid/{user_uuid}", response_model=UserResponse)
async def get_user_by_uuid(user_uuid: str, db: AsyncSession = Depends(get_db_session), _: None = Depends(get_current_user)):
    db_user = await user_service.get_user_by_uuid(db, user_uuid)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

# Edit user by UUID
@router.put("/users/by-uuid/{user_uuid}", response_model=UserResponse)
async def edit_user_by_uuid_endpoint(user_uuid: str, update_data: UserUpdate, db: AsyncSession = Depends(get_db_session), _: None = Depends(get_current_user)):
    user = await user_service.edit_user_by_uuid(db, user_uuid, update_data.model_dump())
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# Delete user by Email
@router.delete("/users/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_email_endpoint(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db_session)):
    # Authenticate user
    user = await user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user or user.email != form_data.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(form_data.username, form_data.password)
    # Proceed with deletion
    success = await user_service.delete_user_by_email(db, form_data.username)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"detail": "User successfully deleted"}

# Login
@router.post("/users/login", response_model=UserWithToken)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db_session)):
    # Authenticate user
    user = await user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = user_service.create_access_token(data={"sub": user.uuid})
    refresh_token = user_service.create_refresh_token(data={"sub": user.uuid})
    user_response = UserResponse.model_validate(user, from_attributes=True).model_dump()
    token_data = Token(access_token=access_token, refresh_token=refresh_token)
    response_data = UserWithToken(user=user_response, token=token_data)
    response = JSONResponse(content=response_data.model_dump())
    return response

@router.post("/users/refreshtoken", response_model=Token)
async def refresh_access_token(token_query: RefreshTokenQuery = Body(...), db: AsyncSession = Depends(get_db_session)):
    refresh_token = token_query.refresh_token
    if refresh_token is None or not (uuid := await user_service.validate_token(db, refresh_token)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    access_token = user_service.create_access_token(data={"sub": uuid})
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")