import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from database.database import AsyncSessionLocal
from database.repositories.guild_repository import GuildRepository

class AntiNukeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_delete_history = defaultdict(list)
        self.channel_create_history = defaultdict(list)
        self.role_delete_history = defaultdict(list)
        self.role_create_history = defaultdict(list)
        self.ban_history = defaultdict(list)
        self.kick_history = defaultdict(list)

        # Thresholds for each action
        self.thresholds = {
            "channel_delete": 3,
            "channel_create": 3,
            "role_delete": 3,
            "role_create": 3,
            "ban": 2,
            "kick": 3
        }
        self.window = 10  # seconds

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        if not guild:
            return

        # Get settings
        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(guild.id)

        if not settings or settings.protection_level != "red":
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.created_at > discord.utils.utcnow() - timedelta(seconds=60):
                    user = entry.user
                    if user.id == guild.owner_id:
                        return

                    self.channel_delete_history[user.id].append(discord.utils.utcnow())
                    await self.check_threshold(user.id, guild, "channel_delete")
        except discord.Forbidden:
            pass

    async def check_threshold(self, user_id: int, guild: discord.Guild, action_type: str):
        history = getattr(self, f"{action_type}_history", {})
        hist = history.get(user_id, [])
        now = discord.utils.utcnow()

        # Clean old entries
        history[user_id] = [ts for ts in hist if (now - ts).total_seconds() < self.window]

        threshold = self.thresholds.get(action_type, 3)

        if len(history[user_id]) >= threshold:
            # Nuke detected
            member = guild.get_member(user_id)
            if member:
                try:
                    await member.ban(reason=f"Anti-Nuke: {action_type} em massa detectado")
                except discord.Forbidden:
                    pass

            # Log the action
            async with AsyncSessionLocal() as session:
                from database.models import SecurityLog
                log = SecurityLog(
                    guild_id=guild.id,
                    user_id=str(user_id),
                    action=f"nuke_{action_type}",
                    details=f"Nuke detectado: {len(history[user_id])} {action_type}s em {self.window}s",
                    severity="high"
                )
                session.add(log)
                await session.commit()

            # Clear history after ban
            history[user_id] = []

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        if not guild:
            return

        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(guild.id)

        if not settings or settings.protection_level != "red":
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.created_at > discord.utils.utcnow() - timedelta(seconds=60):
                    user = entry.user
                    if user.id == guild.owner_id:
                        return

                    self.channel_create_history[user.id].append(discord.utils.utcnow())
                    await self.check_threshold(user.id, guild, "channel_create")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild
        if not guild:
            return

        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(guild.id)

        if not settings or settings.protection_level != "red":
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.created_at > discord.utils.utcnow() - timedelta(seconds=60):
                    user = entry.user
                    if user.id == guild.owner_id:
                        return

                    self.role_delete_history[user.id].append(discord.utils.utcnow())
                    await self.check_threshold(user.id, guild, "role_delete")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        guild = role.guild
        if not guild:
            return

        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(guild.id)

        if not settings or settings.protection_level != "red":
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.created_at > discord.utils.utcnow() - timedelta(seconds=60):
                    user = entry.user
                    if user.id == guild.owner_id:
                        return

                    self.role_create_history[user.id].append(discord.utils.utcnow())
                    await self.check_threshold(user.id, guild, "role_create")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(guild.id)

        if not settings or settings.protection_level != "red":
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.created_at > discord.utils.utcnow() - timedelta(seconds=60):
                    admin = entry.user
                    if admin.id == guild.owner_id:
                        return

                    self.ban_history[admin.id].append(discord.utils.utcnow())
                    await self.check_threshold(admin.id, guild, "ban")
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(guild.id)

        if not settings or settings.protection_level != "red":
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.created_at > discord.utils.utcnow() - timedelta(seconds=60):
                    admin = entry.user
                    if admin.id == guild.owner_id:
                        return

                    self.kick_history[admin.id].append(discord.utils.utcnow())
                    await self.check_threshold(admin.id, guild, "kick")
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(AntiNukeCog(bot))