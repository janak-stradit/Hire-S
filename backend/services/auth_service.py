from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.user_repository import UserRepository
from backend.schemas.user import UserCreate
from backend.services.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.candidates = CandidateRepository(session)

    async def register(self, payload: UserCreate) -> User:
        existing = await self.users.get_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = await self.users.create(
            email=str(payload.email), password_hash=hash_password(payload.password), role="candidate"
        )
        if user.role == "candidate":
            await self.candidates.create_empty(user.id)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def bootstrap_manager(self, email: str, password: str, role: str) -> User:
        existing = await self.users.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = await self.users.create(
            email=email, password_hash=hash_password(password), role=role
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, email: str, password: str) -> str:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        return create_access_token(user.id)
