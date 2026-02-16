"""
Seed Users Script.
Creates initial Admin and Demo users in the database.

Usage:
    python -m backend.scripts.seed_users
"""

import asyncio
import logging
import uuid
from datetime import datetime

from sqlalchemy import select

# Import database and models
from backend.core.database import AsyncSessionLocal
from backend.models.user_settings import User, UserPreferences, UserProfile

# Import hashing function (re-use from auth_api or re-implement if lazy imports issue)
try:
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

except (ImportError, AttributeError, Exception):
    # Fallback for dev environment without passlib
    import hashlib

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_USERS = [
    {
        "email": "admin@agentic-trader.com",
        "password": "admin@123",
        "role": "admin",
        "full_name": "System Administrator",
        "tenant_id": "tenant-admin-001",
    },
    {
        "email": "demo@agentic-trader.com",
        "password": "demo@123",
        "role": "demo",
        "full_name": "Demo User",
        "tenant_id": "tenant-demo-001",
    },
]


async def seed_users():
    logger.info("🌱 Starting user seeding...")


async def seed_users():
    logger.info("🌱 Starting user seeding...")

    async with AsyncSessionLocal() as db:
        try:
            # Set RLS context using SET syntax
            from sqlalchemy import text

            await db.execute(text("SET app.current_tenant = 'system_seed'"))
            logger.info("✅ Set app.current_tenant to system_seed")
        except Exception as e:
            logger.warning(f"⚠️ Failed to set app.current_tenant: {e}")

        for user_data in SEED_USERS:
            # Check if exists
            result = await db.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"User {user_data['email']} already exists. Skipping.")
                continue

            user_id = str(uuid.uuid4())

            # Create User
            new_user = User(
                id=user_id,
                email=user_data["email"],
                password_hash=hash_password(user_data["password"]),
                tenant_id=user_data["tenant_id"],
                role=user_data["role"],
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
            )
            db.add(new_user)

            # Create Profile
            profile = UserProfile(
                id=str(uuid.uuid4()), user_id=user_id, full_name=user_data["full_name"]
            )
            db.add(profile)

            # Create Preferences
            preferences = UserPreferences(id=str(uuid.uuid4()), user_id=user_id)
            db.add(preferences)

            logger.info(f"✨ Created user: {user_data['email']} ({user_data['role']})")

        await db.commit()
        logger.info("✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_users())
