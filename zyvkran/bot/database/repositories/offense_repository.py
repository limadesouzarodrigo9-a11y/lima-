from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserOffense
from datetime import datetime

class OffenseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_offenses(self, guild_id: int, user_id: str):
        result = await self.session.execute(
            select(UserOffense).filter(
                UserOffense.guild_id == guild_id,
                UserOffense.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def increment_offense(self, guild_id: int, user_id: str):
        offense = await self.get_offenses(guild_id, user_id)
        if not offense:
            offense = UserOffense(
                guild_id=guild_id,
                user_id=user_id,
                offense_count=1,
                severity_level=1,
                last_offense_at=datetime.utcnow()
            )
            self.session.add(offense)
        else:
            offense.offense_count += 1
            offense.last_offense_at = datetime.utcnow()
            # Escalate severity every 3 offenses
            if offense.offense_count % 3 == 0:
                offense.severity_level = min(offense.severity_level + 1, 3)

        await self.session.commit()
        return offense
