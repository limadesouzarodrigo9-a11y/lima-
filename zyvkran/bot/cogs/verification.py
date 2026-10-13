import discord
from discord.ext import commands

from database.database import AsyncSessionLocal
from database.repositories.verification_repository import VerificationRepository
from messages.messages import MESSAGES
from utils.embeds import Embeds


VERIFICATION_CHANNELS = {"🔒・backup", "🔐・backup"}


class VerificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(VerificationView())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel and message.channel.name in VERIFICATION_CHANNELS:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

    async def send_verification_message(self, channel: discord.TextChannel):
        """Publishes one verification panel in the configured backup channel."""
        async for message in channel.history(limit=20):
            if message.author.id == self.bot.user.id and any(
                embed.title == MESSAGES["verification"]["title"] for embed in message.embeds
            ):
                return

        msg = MESSAGES["verification"]
        embed = Embeds.create_standard(
            title=msg["title"],
            description=msg["description"],
            color=0x2F3136,
        )
        await channel.send(embed=embed, view=VerificationView())

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel) and channel.name in VERIFICATION_CHANNELS:
            await self.send_verification_message(channel)


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label=MESSAGES["verification"]["button_verify"],
        style=discord.ButtonStyle.green,
        custom_id="verify_button",
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer immediately to avoid "Unknown Interaction" errors
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            return await interaction.followup.send(
                "Este recurso so pode ser usado em um servidor.", ephemeral=True
            )

        async with AsyncSessionLocal() as session:
            repo = VerificationRepository(session)
            is_verified = await repo.is_verified(guild.id, str(member.id))
            if not is_verified:
                await repo.verify_user(guild.id, str(member.id))

        roles = [
            role
            for role in (
                discord.utils.get(guild.roles, name="Verificado"),
                discord.utils.get(guild.roles, name="Membro"),
                discord.utils.get(guild.roles, name="👤 Membro"),
            )
            if role and role not in member.roles
        ]
        if roles:
            try:
                await member.add_roles(*roles, reason="Verificacao concluida")
            except discord.Forbidden:
                return await interaction.followup.send(
                    "A verificacao foi registrada, mas o bot nao conseguiu atribuir o cargo. "
                    "Verifique a hierarquia dos cargos.",
                    ephemeral=True,
                )

        message = (
            MESSAGES["verification"]["already_verified"]
            if is_verified
            else MESSAGES["verification"]["success"]
        )
        await interaction.followup.send(message, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificationCog(bot))
