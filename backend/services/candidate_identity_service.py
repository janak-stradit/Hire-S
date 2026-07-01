"""Candidate identity normalization and deduplication.

Every sourcing cycle can rediscover the same candidate from Excel, LinkedIn,
Naukri, ATS, or future portals. This service prevents duplicate candidate master
records by comparing stable identities such as email, phone, LinkedIn profile,
and source-specific external IDs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.candidate import CandidateIdentity
from backend.models.user import User
from backend.services.security import hash_password

EXTERNAL_PROFILE_SOURCES = {"greenhouse", "icims", "indeed", "linkedin", "naukri", "oracle"}


@dataclass(frozen=True)
class IdentityValue:
    identity_type: str
    normalized_value: str
    primary: bool = False


def normalize_email(value: str) -> str:
    """Normalize email for reliable exact-match identity lookup."""
    return value.strip().casefold()


def normalize_phone(value: str | None) -> str | None:
    """Keep only digits so phone values compare consistently across sources."""
    digits = re.sub(r"\D", "", value or "")
    return digits if len(digits) >= 7 else None


def normalize_linkedin(value: str | None) -> str | None:
    """Convert LinkedIn URLs into one canonical profile key."""
    raw = (value or "").strip()
    if not raw:
        return None
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = parsed.netloc.casefold().removeprefix("www.")
    path = re.sub(r"/+", "/", parsed.path).rstrip("/").casefold()
    if host not in {"linkedin.com", "in.linkedin.com"} or not path:
        return None
    return f"linkedin.com{path}"


def candidate_identities(candidate) -> list[IdentityValue]:
    """Build all identity keys that can map a source row to one candidate."""
    identities = [IdentityValue("email", normalize_email(candidate.email), True)]
    phone = normalize_phone(candidate.phone)
    linkedin = normalize_linkedin(candidate.linkedin_url)
    if phone:
        identities.append(IdentityValue("phone", phone))
    if linkedin:
        identities.append(IdentityValue("linkedin", linkedin))

    source_type = candidate.source_type.strip().casefold()
    external_id = (candidate.external_profile_id or "").strip()
    if not external_id and source_type in EXTERNAL_PROFILE_SOURCES:
        external_id = (candidate.source_reference or "").strip()
    if external_id:
        identities.append(IdentityValue(f"external:{source_type}", external_id.casefold()))
    return list({(item.identity_type, item.normalized_value): item for item in identities}.values())


class CandidateIdentityService:
    """Resolve existing candidate users or create a new candidate identity."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve_or_create_user(
        self, candidate
    ) -> tuple[User, bool, list[IdentityValue]]:
        """Find the candidate by known identities, or create a user shell.

        The user shell lets candidate profile, resume, application, and validator
        rows point to one master ID even when the source is not a self-service
        portal account.
        """
        identities = candidate_identities(candidate)
        predicates = [
            (CandidateIdentity.identity_type == item.identity_type)
            & (CandidateIdentity.normalized_value == item.normalized_value)
            for item in identities
        ]
        matched = list((await self.session.scalars(
            select(CandidateIdentity).where(or_(*predicates))
        )).all())
        candidate_ids = {item.candidate_id for item in matched}
        if len(candidate_ids) > 1:
            # Multiple candidate IDs matching one source row means the identity
            # graph is inconsistent; automatic merge would be unsafe.
            raise HTTPException(
                status_code=409,
                detail="Candidate identifiers belong to different profiles; manual identity review is required.",
            )

        user = await self.session.get(User, next(iter(candidate_ids))) if candidate_ids else None
        if not user:
            user = await self.session.scalar(
                select(User).where(User.email == normalize_email(candidate.email))
            )
        created = user is None
        if created:
            user = User(
                id=candidate.candidate_id or str(uuid4()),
                email=normalize_email(candidate.email),
                password_hash=hash_password(str(uuid4())),
                role="candidate",
                is_active=True,
            )
            self.session.add(user)
            await self.session.flush()

        return user, created, identities

    async def register(
        self, candidate_id: str, source_type: str, identities: list[IdentityValue]
    ) -> None:
        """Attach new identities to the candidate or refresh last-seen metadata."""
        now = datetime.now(UTC)
        for value in identities:
            identity = await self.session.scalar(
                select(CandidateIdentity).where(
                    CandidateIdentity.identity_type == value.identity_type,
                    CandidateIdentity.normalized_value == value.normalized_value,
                )
            )
            if identity:
                if identity.candidate_id != candidate_id:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Conflicting candidate {value.identity_type} identity requires manual review.",
                    )
                identity.last_seen_at = now
                continue
            self.session.add(CandidateIdentity(
                candidate_id=candidate_id,
                identity_type=value.identity_type,
                normalized_value=value.normalized_value,
                source_type=source_type,
                is_primary=value.primary,
            ))
        await self.session.flush()
