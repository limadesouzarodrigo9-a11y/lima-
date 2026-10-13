import discord
import time
from discord import app_commands
from messages.messages import MESSAGES
from utils.embeds import Embeds
from database.database import AsyncSessionLocal
from database.repositories.guild_repository import GuildRepository

class TermsOfUseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.created_at = time.time()

    @discord.ui.button(label=MESSAGES["terms_of_use"]["button_accept"], style=discord.ButtonStyle.green, custom_id="terms_accept")
    async def accept_terms(self, interaction: discord.Interaction, button: discord.ui.Button):
        elapsed = time.time() - self.created_at
        if elapsed < 15:
            remaining = int(15 - elapsed)
            await interaction.response.send_message(
                f'{MESSAGES["terms_of_use"]["wait_message"]} ({remaining}s restantes)',
                ephemeral=True
            )
            return

        # After accepting terms, proceed to PixKeyModal (the "pre-ready" flow)
        try:
            await interaction.response.send_modal(PixKeyModal())
        except discord.errors.NotFound:
            # Fallback: if interaction expired, send a follow-up message
            await interaction.followup.send(
                "⏰ A interação expirou. Por favor, clique novamente em 'Iniciar' para recomeçar.",
                ephemeral=True
            )

class PixKeyModal(discord.ui.Modal, title="Configuração de Pagamento"):
    pix_key = discord.ui.TextInput(
        label="Chave Pix",
        placeholder="Digite sua chave Pix aqui...",
        required=True
    )
    pix_type = discord.ui.TextInput(
        label="Tipo da Chave",
        placeholder="CPF, Email, Telefone ou Aleatória",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            await repo.update_settings(
                interaction.guild_id,
                pix_key=self.pix_key.value,
                pix_type=self.pix_type.value
            )

        # Trigger server creation
        from cogs.setup import ServerSetupCog
        cog = interaction.client.get_cog("ServerSetupCog")
        if cog:
            await cog.create_pre_ready_server(interaction)
        else:
            await interaction.response.send_message("Erro interno: SetupCog não encontrado.", ephemeral=True)

class DespertarView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=MESSAGES["despertar"]["buttons"]["start"], style=discord.ButtonStyle.green, custom_id="despertar_start")
    async def start_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = Embeds.create_standard(
            title=MESSAGES["terms_of_use"]["title"],
            description=MESSAGES["terms_of_use"]["description"]
        )
        await interaction.response.send_message(embed=embed, view=TermsOfUseView(), ephemeral=True)
