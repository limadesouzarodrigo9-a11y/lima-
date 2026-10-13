import discord
from discord.ext import commands
from discord import app_commands
from database.database import AsyncSessionLocal
from database.repositories.guild_repository import GuildRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.order_repository import OrderRepository
from database.repositories.ticket_repository import TicketRepository
from utils.embeds import Embeds

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="painel", description="Painel administrativo do bot")
    async def painel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("⚠️ Apenas administradores podem acessar o painel.", ephemeral=True)

        # Get stats
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            from database.models import Product, Order, Ticket

            product_count = await session.execute(select(func.count(Product.id)).filter(Product.guild_id == interaction.guild_id))
            product_count = product_count.scalar() or 0

            order_count = await session.execute(select(func.count(Order.id)).filter(Order.guild_id == interaction.guild_id))
            order_count = order_count.scalar() or 0

            ticket_count = await session.execute(select(func.count(Ticket.id)).filter(Ticket.guild_id == interaction.guild_id))
            ticket_count = ticket_count.scalar() or 0

        embed = Embeds.create_standard(
            title="╔══════════════════════════╗\n║      PAINEL DO BOT       ║\n╚══════════════════════════╝",
            description=f"""
📊 **Estatísticas do Servidor**

🛒 Produtos: {product_count}
💰 Pedidos: {order_count}
🎫 Tickets: {ticket_count}
👥 Membros: {interaction.guild.member_count}
            """,
            color=0x2F3136
        )

        view = AdminPanelView()
        await interaction.response.send_message(embed=embed, view=view)

class AdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛡️ Proteção", style=discord.ButtonStyle.blurple, custom_id="admin_protection")
    async def protection(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed=Embeds.create_standard(
                title="Configurações de Proteção",
                description="Gerencie os canais 'Trap' (onde qualquer mensagem resulta em banimento permanente)."
            ),
            view=TrapConfigView(),
            ephemeral=True
        )

    @discord.ui.button(label="🛒 Loja", style=discord.ButtonStyle.green, custom_id="admin_shop")
    async def shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=Embeds.create_standard(title="Configurações da Loja", description="Selecione o canal onde o catálogo de vendas deve ser publicado."), view=ShopConfigView(), ephemeral=True)

    @discord.ui.button(label="🎫 Tickets", style=discord.ButtonStyle.grey, custom_id="admin_tickets")
    async def tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🎫 Gerenciamento de tickets será implementado em breve.", ephemeral=True)

    @discord.ui.button(label="👥 Cargos", style=discord.ButtonStyle.grey, custom_id="admin_roles")
    async def roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👥 Gerenciamento de cargos será implementado em breve.", ephemeral=True)

    @discord.ui.button(label="📋 Logs", style=discord.ButtonStyle.grey, custom_id="admin_logs")
    async def logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📋 Configurações de logs serão implementadas em breve.", ephemeral=True)

    @discord.ui.button(label="🔐 Verificação", style=discord.ButtonStyle.grey, custom_id="admin_verification")
    async def verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔐 Configurações de verificação serão implementadas em breve.", ephemeral=True)

    @discord.ui.button(label="💾 Backup", style=discord.ButtonStyle.grey, custom_id="admin_backup")
    async def backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("💾 Sistema de backup será implementado em breve.", ephemeral=True)

    @discord.ui.button(label="📊 Estatísticas", style=discord.ButtonStyle.grey, custom_id="admin_stats")
    async def stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Re-send the panel
        embed = Embeds.create_standard(
            title="📊 Estatísticas",
            description="Carregando estatísticas...",
            color=0x2F3136
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚙️ Configurações", style=discord.ButtonStyle.red, custom_id="admin_settings")
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SettingsModal())

class ShopConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.select(cls=discord.ui.ChannelSelect, placeholder="Selecione o canal da loja...")
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            await repo.update_settings(interaction.guild_id, shop_channel_id=str(channel.id))

        await interaction.response.send_message(f"✅ Canal da loja definido para {channel.mention}", ephemeral=True)

class TrapConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=600)

    @discord.ui.select(cls=discord.ui.ChannelSelect, placeholder="Adicione um canal Trap...")
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect):
        channel = select.values[0]
        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            settings = await repo.get_settings(interaction.guild_id)

            current_traps = settings.trap_channels.split(",") if settings and settings.trap_channels else []
            current_traps = [t for t in current_traps if t] # Remove empty strings

            channel_id = str(channel.id)
            if channel_id in current_traps:
                await interaction.response.send_message(f"❌ O canal {channel.mention} já é um canal trap.", ephemeral=True)
                return

            current_traps.append(channel_id)
            new_traps = ",".join(current_traps)
            await repo.update_settings(interaction.guild_id, trap_channels=new_traps)

        await interaction.response.send_message(f"✅ Canal {channel.mention} adicionado aos canais Trap. Qualquer pessoa que escrever lá será banida!", ephemeral=True)

class SettingsModal(discord.ui.Modal, title="Configurações do Servidor"):
    pix_key = discord.ui.TextInput(
        label="Chave Pix",
        placeholder="Digite sua nova chave Pix...",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.pix_key.value:
            async with AsyncSessionLocal() as session:
                repo = GuildRepository(session)
                await repo.update_settings(interaction.guild_id, pix_key=self.pix_key.value)

            await interaction.response.send_message("✅ Chave Pix atualizada com sucesso!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Nenhuma alteração foi feita.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))