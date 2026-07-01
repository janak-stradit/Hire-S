from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.config.settings import get_settings
from backend.schemas.user import LoginRequest, ManagerBootstrapRequest, Token, UserCreate, UserRead
from backend.services.auth_service import AuthService
from backend.api.dependencies import get_current_user
from backend.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=201)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    return await AuthService(session).register(payload)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    access_token = await AuthService(session).login(str(payload.email), payload.password)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/bootstrap-manager", response_model=UserRead, status_code=201, include_in_schema=False)
async def bootstrap_manager(
    payload: ManagerBootstrapRequest,
    bootstrap_key: str | None = Header(default=None, alias="X-HireX-Bootstrap-Key"),
    session: AsyncSession = Depends(get_session),
):
    configured_key = get_settings().manager_bootstrap_key
    if not configured_key:
        raise HTTPException(status_code=404, detail="Not found")
    if bootstrap_key != configured_key:
        raise HTTPException(status_code=403, detail="Invalid bootstrap key")
    return await AuthService(session).bootstrap_manager(str(payload.email), payload.password, payload.role)
