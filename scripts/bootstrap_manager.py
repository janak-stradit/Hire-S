import argparse
import asyncio
import secrets
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from backend.database.session import AsyncSessionLocal
from backend.models.user import User
from backend.services.security import hash_password


async def bootstrap(email: str, role: str, generate_password: bool = False) -> None:
    if generate_password:
        password = f"Hx-{secrets.token_urlsafe(12)}!9"
    else:
        password = getpass("Manager password: ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            raise SystemExit("Passwords do not match")
    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters")
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(User).where(User.email == email.lower()))
        if existing:
            existing.password_hash = hash_password(password)
            existing.role = role
            existing.is_active = True
        else:
            session.add(User(
                email=email.lower(), password_hash=hash_password(password), role=role, is_active=True
            ))
        await session.commit()
    print(f"Created or updated {role} account for {email.lower()}")
    if generate_password:
        print(f"Generated password: {password}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a HireX manager account securely.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", choices=("admin", "hr", "recruiter"), default="admin")
    parser.add_argument("--generate-password", action="store_true")
    args = parser.parse_args()
    asyncio.run(bootstrap(args.email, args.role, args.generate_password))


if __name__ == "__main__":
    main()
