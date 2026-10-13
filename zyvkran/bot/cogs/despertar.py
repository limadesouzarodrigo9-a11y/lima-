import discord
from discord import app_commands
from discord.ext import commands
import logging
from messages.messages import MESSAGES
from utils.embeds import Embeds
from views.setup_views import DespertarView

logger = logging.getLogger("bot")

class Despertar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="despertar", description="Inicia a configuração do servidor")
    async def despertar(self, interaction: discord.Interaction):
        if interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message(MESSAGES["errors"]["not_owner"], ephemeral=True)

        try:
            embed = Embeds.create_standard(
                title=MESSAGES["despertar"]["title"],
                description=MESSAGES["despertar"]["description"]
            )
            view = DespertarView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in despertar command: {e}")
            try:
                await interaction.response.send_message("❌ Ocorreu um erro ao processar o comando. Tente novamente.", ephemeral=True)
            except:
                try:
                    await interaction.followup.send("❌ Ocorreu um erro ao processar o comando. Tente novamente.", ephemeral=True)
                except:
                    pass

async def setup(bot):
    await bot.add_cog(Despertar(bot))