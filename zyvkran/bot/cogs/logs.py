import discord
from discord.ext import commands
from datetime import datetime
from database.database import AsyncSessionLocal
from utils.embeds import Embeds

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_cache = {}

    async def get_log_channel(self, guild: discord.Guild):
        """Gets the log channel for the guild from cache or database."""
        if guild.id in self.log_channel_cache:
            return self.log_channel_cache[guild.id]

        from config import Config
        if Config.LOG_CHANNEL_ID:
            channel = guild.get_channel(Config.LOG_CHANNEL_ID)
            if channel:
                self.log_channel_cache[guild.id] = channel
                return channel

        log_channel = discord.utils.get(guild.text_channels, name="📝・logs")
        if log_channel:
            self.log_channel_cache[guild.id] = log_channel
        return log_channel

    async def emit_log(self, guild: discord.Guild, title: str, description: str, color=0x2F3136, fields=None, thumbnail=None):
        """Centralized method to send logs across the bot."""
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title=title,
            description=description,
            color=color,
            thumbnail=thumbnail
        )
        if fields:
            for name, value in fields.items():
                embed.add_field(name=name, value=value, inline=True)

        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()

    async def on_member_join(self, member: discord.Member):
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="📥 Entrada de Membro",
            description=f"{member.mention} entrou no servidor.",
            color=0x00FF00
        )
        embed.add_field(name="Usuário", value=f"{member.name}#{member.discriminator}")
        embed.add_field(name="ID", value=str(member.id))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        log_channel = await self.get_log_channel(member.guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="📤 Saída de Membro",
            description=f"{member.mention} saiu do servidor.",
            color=0xFF0000
        )
        embed.add_field(name="Usuário", value=f"{member.name}#{member.discriminator}")
        embed.add_field(name="ID", value=str(member.id))
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        log_channel = await self.get_log_channel(guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="🔨 Banimento",
            description=f"{user.mention} foi banido.",
            color=0xFF0000
        )
        embed.add_field(name="Usuário", value=f"{user.name}#{user.discriminator}")
        embed.add_field(name="ID", value=str(user.id))
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        log_channel = await self.get_log_channel(message.guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="🗑️ Mensagem Excluída",
            description=f"Mensagem de {message.author.mention} excluída em {message.channel.mention}",
            color=0xFFA500
        )
        embed.add_field(name="Conteúdo", value=message.content[:1024] or "_(Sem conteúdo)_")
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return

        if before.guild is None:
            return

        log_channel = await self.get_log_channel(before.guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="✏️ Mensagem Editada",
            description=f"Mensagem de {before.author.mention} editada em {before.channel.mention}",
            color=0xFFFF00
        )
        embed.add_field(name="Antes", value=before.content[:1024] or "_(Sem conteúdo)_")
        embed.add_field(name="Depois", value=after.content[:1024] or "_(Sem conteúdo)_")
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_channel = await self.get_log_channel(channel.guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="📝 Canal Criado",
            description=f"Canal {channel.mention} criado.",
            color=0x00FF00
        )
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_channel = await self.get_log_channel(channel.guild)
        if not log_channel:
            return

        embed = Embeds.create_standard(
            title="🗑️ Canal Excluído",
            description=f"Canal **{channel.name}** foi excluído.",
            color=0xFF0000
        )
        embed.timestamp = datetime.utcnow()

        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(LogsCog(bot))