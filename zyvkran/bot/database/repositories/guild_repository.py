from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Guild, GuildSettings

class GuildRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_guild(self, guild_id: int):
        result = await self.session.execute(select(Guild).filter(Guild.id == guild_id))
        return result.scalar_one_or_none()

    async def create_guild(self, guild_id: int, owner_id: str):
        guild = Guild(id=guild_id, owner_id=owner_id)
        self.session.add(guild)
        await self.session.commit()
        return guild

    async def get_settings(self, guild_id: int):
        result = await self.session.execute(
            select(GuildSettings).filter(GuildSettings.guild_id == guild_id)
        )
        return result.scalar_one_or_none()

    async def update_settings(self, guild_id: int, **kwargs):
        settings = await self.get_settings(guild_id)
        if not settings:
            settings = GuildSettings(guild_id=guild_id, **kwargs)
            self.session.add(settings)
        else:
            for key, value in kwargs.items():
                setattr(settings, key, value)
        await self.session.commit()
        return settings
