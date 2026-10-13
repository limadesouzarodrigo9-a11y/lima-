from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Verification
from datetime import datetime

class VerificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def verify_user(self, guild_id: int, user_id: str):
        result = await self.session.execute(
            select(Verification).filter(Verification.guild_id == guild_id, Verification.user_id == user_id)
        )
        verification = result.scalar_one_or_none()
        if not verification:
            verification = Verification(guild_id=guild_id, user_id=user_id, is_verified=True, verified_at=datetime.utcnow())
            self.session.add(verification)
        else:
            verification.is_verified = True
            verification.verified_at = datetime.utcnow()

        await self.session.commit()
        return verification

    async def is_verified(self, guild_id: int, user_id: str) -> bool:
        result = await self.session.execute(
            select(Verification).filter(Verification.guild_id == guild_id, Verification.user_id == user_id)
        )
        verification = result.scalar_one_or_none()
        return verification.is_verified if verification else False
