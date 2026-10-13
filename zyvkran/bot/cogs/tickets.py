import asyncio
import io
import logging

import discord
from discord import app_commands
from discord.ext import commands

from database.database import AsyncSessionLocal
from database.repositories.ticket_repository import TicketRepository
from messages.messages import MESSAGES
from utils.embeds import Embeds
from config import Config


logger = logging.getLogger("bot")


def is_staff(member: discord.Member, owner_id: int) -> bool:
    if member.id == owner_id or member.guild_permissions.administrator:
        return True
    return any(
        marker in role.name.lower()
        for role in member.roles
        for marker in ("administrador", "moderador", "suporte", "vendedor")
    )


class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(TicketTypeSelectView())

    @app_commands.command(name="ticket", description="Publica a central de atendimento.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket(self, interaction: discord.Interaction):
        msg = MESSAGES["tickets"]
        embed = Embeds.create_standard(
            title=msg["hub_title"],
            description=msg["hub_description"],
            color=0x2F3136,
        )
        await interaction.response.send_message(embed=embed, view=TicketTypeSelectView())

    async def create_ticket(self, interaction: discord.Interaction, category: str):
        guild = interaction.guild
        user = interaction.user
        if guild is None or not isinstance(user, discord.Member):
            return await interaction.response.send_message(
                "Este recurso so funciona em um servidor.", ephemeral=True
            )

        # 1. Ticket Limit Check
        async with AsyncSessionLocal() as session:
            repo = TicketRepository(session)
            open_tickets = await repo.get_open_tickets_count(guild.id, str(user.id))
            if open_tickets >= Config.MAX_OPEN_TICKETS_PER_USER:
                return await interaction.response.send_message(
                    f"Você já possui o limite máximo de tickets abertos ({Config.MAX_OPEN_TICKETS_PER_USER}). Por favor, aguarde o atendimento ou feche um ticket existente.",
                    ephemeral=True
                )

        ticket_category = discord.utils.get(guild.categories, name="Tickets")
        if ticket_category is None:
            ticket_category = await guild.create_category("Tickets", reason="Central de atendimento")

        bot_member = guild.me or (self.bot.user and guild.get_member(self.bot.user.id))
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
        }
        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
        for role in guild.roles:
            if any(marker in role.name.lower() for marker in ("administrador", "moderador", "suporte", "vendedor")):
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        channel_name = f"ticket-{user.id}"
        existing = discord.utils.get(guild.text_channels, name=channel_name, category=ticket_category)
        if existing:
            return await interaction.response.send_message(
                f"Voce ja possui um ticket aberto: {existing.mention}", ephemeral=True
            )
        channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category,
            overwrites=overwrites,
            reason=f"Ticket aberto por {user}",
        )

        async with AsyncSessionLocal() as session:
            repo = TicketRepository(session)
            ticket = await repo.create_ticket(
                guild_id=guild.id,
                user_id=str(user.id),
                channel_id=str(channel.id),
                category=category,
            )

        msg = MESSAGES["tickets"]
        embed = Embeds.create_standard(
            title=msg["welcome_title"],
            description=msg["welcome_description"].format(
                user=user.mention,
                category=msg["options"].get(category, category),
            ),
            color=0x2F3136,
        )
        embed.set_footer(text=f"ID do ticket: {ticket.id}")
        await channel.send(embed=embed, view=TicketManagementView(ticket.id))
        await interaction.response.send_message(
            f"Ticket criado: {channel.mention}", ephemeral=True
        )


class TicketTypeSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Escolha o tipo de atendimento...",
        custom_id="ticket_type_select",
        options=[
            discord.SelectOption(label=MESSAGES["tickets"]["options"]["suporte"], value="suporte"),
            discord.SelectOption(label=MESSAGES["tickets"]["options"]["compras"], value="compras"),
            discord.SelectOption(label=MESSAGES["tickets"]["options"]["denuncia"], value="denuncia"),
            discord.SelectOption(label=MESSAGES["tickets"]["options"]["ajuda"], value="ajuda"),
            discord.SelectOption(label=MESSAGES["tickets"]["options"]["pos_venda"], value="pos_venda"),
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        cog = interaction.client.get_cog("TicketsCog")
        if cog is None:
            return await interaction.response.send_message(
                "O sistema de tickets esta indisponivel no momento.", ephemeral=True
            )
        await cog.create_ticket(interaction, select.values[0])


class TicketManagementView(discord.ui.View):
    def __init__(self, ticket_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id

    def _can_manage(self, interaction: discord.Interaction) -> bool:
        return (
            interaction.guild is not None
            and isinstance(interaction.user, discord.Member)
            and is_staff(interaction.user, interaction.guild.owner_id)
        )

    @discord.ui.button(label="Fechar ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._can_manage(interaction):
            return await interaction.response.send_message(
                "Apenas a equipe pode fechar tickets.", ephemeral=True
            )

        async with AsyncSessionLocal() as session:
            repo = TicketRepository(session)
            await repo.close_ticket(self.ticket_id)

        msg = MESSAGES["tickets"]
        embed = Embeds.create_standard(
            title=msg["closed"], description=msg["closed_description"], color=0xFF0000
        )
        await interaction.response.send_message(embed=embed)
        await interaction.channel.send("O canal será fechado em 30 segundos.")
        await asyncio.sleep(30)
        try:
            await interaction.channel.delete(reason="Ticket fechado pela equipe")
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    @discord.ui.button(label="Transcript", style=discord.ButtonStyle.secondary)
    async def transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._can_manage(interaction):
            return await interaction.response.send_message(
                "Apenas a equipe pode gerar transcripts.", ephemeral=True
            )

        lines = []
        async for message in interaction.channel.history(limit=None):
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M")
            lines.append(f"[{timestamp}] {message.author}: {message.content}")
        transcript = "\n".join(reversed(lines))
        file = discord.File(
            io.BytesIO(transcript.encode("utf-8")),
            filename=f"transcript-ticket-{self.ticket_id}.txt",
        )
        await interaction.response.send_message("Transcript gerado.", file=file, ephemeral=True)

    @discord.ui.button(label="Adicionar usuario", style=discord.ButtonStyle.blurple)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._can_manage(interaction):
            return await interaction.response.send_message(
                "Apenas a equipe pode adicionar usuarios.", ephemeral=True
            )
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(label="Excluir canal", style=discord.ButtonStyle.danger)
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._can_manage(interaction):
            return await interaction.response.send_message(
                "Apenas a equipe pode excluir o canal.", ephemeral=True
            )
        await interaction.response.send_message("O canal será fechado em 30 segundos.")
        await asyncio.sleep(30)
        try:
            await interaction.channel.delete(reason="Ticket removido pela equipe")
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


class AddUserModal(discord.ui.Modal, title="Adicionar usuario ao ticket"):
    user_id = discord.ui.TextInput(
        label="ID do usuario", placeholder="Digite o ID do usuario...", required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
        except ValueError:
            return await interaction.response.send_message("ID invalido.", ephemeral=True)

        member = interaction.guild.get_member(user_id)
        if member is None:
            return await interaction.response.send_message("Usuario nao encontrado.", ephemeral=True)
        await interaction.channel.set_permissions(
            member, view_channel=True, send_messages=True, read_message_history=True
        )
        await interaction.response.send_message(
            f"{member.mention} foi adicionado ao ticket.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketsCog(bot))
