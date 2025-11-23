from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api import deps
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserRead, UserCreate
from app.services.auth_service import AuthService


router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, auth_service: AuthService = Depends(deps.get_auth_service)
):
    return await auth_service.register_user(user_in)


@router.post("/login", response_model=Token)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthService = Depends(deps.get_auth_service),
):
    return await auth_service.authenticate_user(
        email=form_data.username, password=form_data.password
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: str = Depends(deps.oauth2_scheme),
    auth_service: AuthService = Depends(deps.get_auth_service),
    current_user: User = Depends(deps.get_current_user),
):
    await auth_service.logout(token)
    return {"message": "Successfully logged out"}
