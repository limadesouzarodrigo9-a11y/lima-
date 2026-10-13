import logging

import discord
from discord import app_commands
from discord.ext import commands


logger = logging.getLogger("bot")


class DormirConfirmationModal(discord.ui.Modal, title="Confirmar modo dormir"):
    confirmation = discord.ui.TextInput(
        label="Digite DORMIR para confirmar",
        placeholder="DORMIR",
        min_length=6,
        max_length=6,
    )

    def __init__(self, cog: "DormirCog"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirmation.value.strip().upper() != "DORMIR":
            return await interaction.response.send_message(
                "Confirmacao invalida. Nenhuma alteracao foi feita.", ephemeral=True
            )
        await self.cog.enable_sleep_mode(interaction)


class DormirCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="dormir",
        description="Remove canais e cargos, mantendo somente o canal atualizando.",
    )
    async def dormir(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None or interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(
                "Apenas o proprietario do servidor pode usar este comando.", ephemeral=True
            )
        await interaction.response.send_modal(DormirConfirmationModal(self))

    async def enable_sleep_mode(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None or interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(
                "Apenas o proprietario do servidor pode usar este comando.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        owner = guild.owner or guild.get_member(guild.owner_id)
        bot_member = guild.me or (self.bot.user and guild.get_member(self.bot.user.id))
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=False, read_message_history=True
            )
        }
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )
        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )

        update_channel = discord.utils.get(guild.text_channels, name="atualizando")
        if update_channel is None:
            update_channel = await guild.create_text_channel(
                "atualizando", overwrites=overwrites, reason="Modo dormir"
            )
        else:
            await update_channel.edit(
                category=None, overwrites=overwrites, reason="Modo dormir"
            )

        deleted_channels = 0
        for channel in sorted(
            (item for item in guild.channels if item.id != update_channel.id),
            key=lambda item: isinstance(item, discord.CategoryChannel),
        ):
            try:
                await channel.delete(reason="Modo dormir ativado pelo proprietario")
                deleted_channels += 1
            except (discord.Forbidden, discord.HTTPException):
                logger.warning("Nao foi possivel remover o canal %s em %s", channel.id, guild.id)

        deleted_roles = 0
        top_role = bot_member.top_role if bot_member else None
        for role in sorted(guild.roles, key=lambda item: item.position, reverse=True):
            if role.is_default() or role.managed:
                continue
            if top_role and role >= top_role:
                continue
            try:
                await role.delete(reason="Modo dormir ativado pelo proprietario")
                deleted_roles += 1
            except (discord.Forbidden, discord.HTTPException):
                logger.warning("Nao foi possivel remover o cargo %s em %s", role.id, guild.id)

        await update_channel.send(
            "Servidor em atualizacao. Apenas o proprietario pode enviar mensagens neste canal."
        )
        await interaction.followup.send(
            f"Modo dormir ativado: {deleted_channels} canais/categorias e {deleted_roles} cargos removidos.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(DormirCog(bot))
