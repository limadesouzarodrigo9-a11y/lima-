import logging

import discord
from discord import app_commands
from discord.ext import commands

from database.database import AsyncSessionLocal
from database.repositories.guild_repository import GuildRepository
from messages.messages import MESSAGES
from utils.embeds import Embeds


logger = logging.getLogger("bot")

TERMS_OF_USE = """Ao continuar, o proprietario confirma que este servidor sera usado somente para a venda de produtos e servicos legais.

Sao proibidos: contas comprometidas, credenciais, cartoes ou dados de pagamento, dados vazados, fraude, golpes e qualquer item que viole a lei ou os termos do Discord. O proprietario e responsavel pelo catalogo, pela entrega e pelo atendimento ao cliente.

Ao aceitar, o bot ativa a protecao maxima: anti-raid, anti-spam, bloqueio de links, controle de mencoes, bloqueio de bots nao autorizados e anti-nuke."""


class TermsAcceptanceView(discord.ui.View):
    def __init__(self, setup_cog: "ServerSetupCog", owner_id: int):
        super().__init__(timeout=900)
        self.setup_cog = setup_cog
        self.owner_id = owner_id

    @discord.ui.button(label="Aceitar termos e cadastrar Pix", style=discord.ButtonStyle.green)
    async def accept_terms(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message(
                MESSAGES["errors"]["not_owner"], ephemeral=True
            )

        await interaction.response.send_modal(PixRegistrationModal(self.setup_cog))


class PixRegistrationModal(discord.ui.Modal):
    def __init__(self, setup_cog: "ServerSetupCog"):
        msg = MESSAGES["server_pre_ready"]["pix_modal"]
        super().__init__(title=msg["title"])
        self.setup_cog = setup_cog

        self.pix_key = discord.ui.TextInput(
            label=msg["pix_key_label"],
            placeholder=msg["pix_key_placeholder"],
            required=True,
            max_length=120,
        )
        self.pix_type = discord.ui.TextInput(
            label=msg["pix_type_label"],
            placeholder=msg["pix_type_placeholder"],
            required=True,
            max_length=50,
        )
        self.add_item(self.pix_key)
        self.add_item(self.pix_type)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None or interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(
                MESSAGES["errors"]["not_owner"], ephemeral=True
            )

        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            if not await repo.get_guild(guild.id):
                await repo.create_guild(guild.id, str(guild.owner_id))
            await repo.update_settings(
                guild_id=guild.id,
                pix_key=self.pix_key.value.strip(),
                pix_type=self.pix_type.value.strip(),
                protection_level="red",
            )

        await self.setup_cog.create_pre_ready_server(interaction)


class StockRequestModal(discord.ui.Modal, title="Solicitar reposicao"):
    product_name = discord.ui.TextInput(
        label="Produto desejado",
        placeholder="Informe o produto que voce gostaria de ver na loja.",
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message(
                "Este recurso so funciona em um servidor.", ephemeral=True
            )

        await interaction.response.send_message("Pedido de reposicao enviado.", ephemeral=True)
        owner = guild.owner or guild.get_member(guild.owner_id)
        if owner:
            try:
                await owner.send(
                    f"Reposicao solicitada em **{guild.name}** por {interaction.user}: "
                    f"{self.product_name.value.strip()}"
                )
            except discord.Forbidden:
                logger.info("Nao foi possivel enviar DM de reposicao ao proprietario de %s", guild.id)


class StockRequestView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Solicitar reposicao",
        style=discord.ButtonStyle.secondary,
        custom_id="stock_request",
    )
    async def request_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StockRequestModal())


class ServerSetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(StockRequestView())

    @app_commands.command(
        name="servidor_pre_pronto",
        description="Cria a estrutura protegida de uma loja legal.",
    )
    async def setup_pre_ready(self, interaction: discord.Interaction):
        await self.show_terms(interaction)

    async def show_terms(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None or interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(
                MESSAGES["errors"]["not_owner"], ephemeral=True
            )

        embed = Embeds.create_standard(
            title="Termos de uso e protecao do servidor",
            description=TERMS_OF_USE,
            color=0xC0392B,
        )
        await interaction.response.send_message(
            embed=embed,
            view=TermsAcceptanceView(self, guild.owner_id),
            ephemeral=True,
        )

    @staticmethod
    def _role(guild: discord.Guild, name: str) -> discord.Role | None:
        return discord.utils.get(guild.roles, name=name)

    async def _ensure_category(self, guild: discord.Guild, name: str) -> discord.CategoryChannel:
        category = discord.utils.get(guild.categories, name=name)
        if category is None:
            category = await guild.create_category(name, reason="Servidor pre-pronto")
        return category

    async def _ensure_text_channel(
        self,
        guild: discord.Guild,
        category: discord.CategoryChannel,
        name: str,
        overwrites: dict,
    ) -> discord.TextChannel:
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel is None:
            return await guild.create_text_channel(
                name,
                category=category,
                overwrites=overwrites,
                reason="Servidor pre-pronto",
            )

        await channel.edit(category=category, overwrites=overwrites, reason="Servidor pre-pronto")
        return channel

    def _overwrites(
        self,
        guild: discord.Guild,
        roles: dict[str, discord.Role],
        *,
        public: bool = False,
        default_can_send: bool = False,
        verified_can_send: bool = False,
        buyers_can_send: bool = False,
    ) -> dict:
        owner = guild.owner or guild.get_member(guild.owner_id)
        bot_member = guild.me or (self.bot.user and guild.get_member(self.bot.user.id))
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=public,
                send_messages=default_can_send,
                read_message_history=public,
            )
        }

        for role_name in ("Proprietario", "Administrador", "Moderador", "Suporte", "Vendedor"):
            role = roles.get(role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=role_name in {"Proprietario", "Administrador", "Moderador"},
                )

        for role_name in ("Verificado", "Membro"):
            role = roles.get(role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=verified_can_send,
                    read_message_history=True,
                )

        buyer = roles.get("Comprador")
        if buyer:
            overwrites[buyer] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=buyers_can_send,
                read_message_history=True,
            )

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
                manage_messages=True,
            )
        return overwrites

    async def _post_once(
        self,
        channel: discord.TextChannel,
        title: str,
        *,
        description: str,
        view: discord.ui.View | None = None,
    ) -> None:
        async for message in channel.history(limit=20):
            if message.author.id != self.bot.user.id:
                continue
            if any(embed.title == title for embed in message.embeds):
                return

        await channel.send(
            embed=Embeds.create_standard(title=title, description=description),
            view=view,
        )

    async def create_pre_ready_server(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None or interaction.user.id != guild.owner_id:
            if interaction.response.is_done():
                await interaction.followup.send(MESSAGES["errors"]["not_owner"], ephemeral=True)
            else:
                await interaction.response.send_message(MESSAGES["errors"]["not_owner"], ephemeral=True)
            return

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=True)

        async with AsyncSessionLocal() as session:
            repo = GuildRepository(session)
            if not await repo.get_guild(guild.id):
                await repo.create_guild(guild.id, str(guild.owner_id))
            await repo.update_settings(guild.id, protection_level="red")

        roles_config = {
            "Proprietario": (discord.Permissions.all(), 0xF1C40F),
            "Administrador": (discord.Permissions(administrator=True), 0xE74C3C),
            "Moderador": (
                discord.Permissions(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_messages=True,
                    kick_members=True,
                    ban_members=True,
                ),
                0x2ECC71,
            ),
            "Suporte": (
                discord.Permissions(view_channel=True, send_messages=True, read_message_history=True),
                0x3498DB,
            ),
            "Vendedor": (
                discord.Permissions(view_channel=True, send_messages=True, read_message_history=True),
                0x1ABC9C,
            ),
            "Comprador": (discord.Permissions.none(), 0x95A5A6),
            "Membro": (discord.Permissions.none(), 0xECF0F1),
            "Verificado": (discord.Permissions.none(), 0x9B59B6),
        }
        roles: dict[str, discord.Role] = {}
        for name, (permissions, color) in roles_config.items():
            role = self._role(guild, name)
            if role is None:
                try:
                    role = await guild.create_role(
                        name=name,
                        permissions=permissions,
                        color=discord.Color(color),
                        reason="Servidor pre-pronto",
                    )
                except discord.HTTPException:
                    logger.exception("Falha ao criar cargo %s em %s", name, guild.id)
                    continue
            roles[name] = role

        owner = guild.owner or guild.get_member(guild.owner_id)
        owner_role = roles.get("Proprietario")
        if owner and owner_role and owner_role not in owner.roles:
            try:
                await owner.add_roles(owner_role, reason="Servidor pre-pronto")
            except discord.Forbidden:
                logger.warning("Sem permissao para atribuir o cargo de proprietario em %s", guild.id)

        server = await self._ensure_category(guild, "server")
        help_category = await self._ensure_category(guild, "help")
        sales = await self._ensure_category(guild, "sales")
        community = await self._ensure_category(guild, "comunidade")
        stock = await self._ensure_category(guild, "estoque")
        products = await self._ensure_category(guild, "produtos")
        others = await self._ensure_category(guild, "others")

        public_readonly = self._overwrites(guild, roles, public=True)
        verified_readonly = self._overwrites(guild, roles)
        verified_chat = self._overwrites(guild, roles, verified_can_send=True)
        buyer_feedback = self._overwrites(guild, roles, buyers_can_send=True)

        no_messages = await self._ensure_text_channel(
            guild, server, "📥・nao-mande-nada", self._overwrites(guild, roles, public=True, default_can_send=True)
        )
        backup = await self._ensure_text_channel(guild, server, "🔒・backup", public_readonly)
        terms = await self._ensure_text_channel(guild, server, "📚・termos", public_readonly)
        attendance = await self._ensure_text_channel(
            guild, help_category, "🛩️・atendimento", verified_readonly
        )
        feedback = await self._ensure_text_channel(guild, sales, "🩶・feedback", buyer_feedback)
        orders = await self._ensure_text_channel(guild, sales, "💬・pedidos", buyer_feedback)
        giveaway = await self._ensure_text_channel(guild, community, "🎁・sorteio", verified_readonly)
        warnings = await self._ensure_text_channel(guild, community, "📣・warn", verified_readonly)
        chat = await self._ensure_text_channel(guild, community, "💬・chat", verified_chat)
        restock = await self._ensure_text_channel(guild, stock, "📦・reestock", verified_readonly)
        request_stock = await self._ensure_text_channel(
            guild, stock, "🗃️・solicitar-stock", verified_readonly
        )

        product_channels = []
        for name in (
            "🏆・acessos",
            "📦・itens-digitais",
            "⚡・assinaturas",
            "🧊・servicos",
            "👥・membros",
            "💼・revendedores",
        ):
            product_channels.append(
                await self._ensure_text_channel(guild, products, name, verified_readonly)
            )

        for name in ("🏆・ferramentas", "📦・recursos", "⚡・integracoes", "🧊・variedades"):
            await self._ensure_text_channel(guild, others, name, verified_readonly)

        from cogs.shop import ProductCatalogView
        from cogs.tickets import TicketTypeSelectView
        from cogs.verification import VerificationView

        await self._post_once(
            no_messages,
            "Canal reservado",
            description=(
                "Nao envie mensagens, arquivos ou links neste canal. Ele e reservado para "
                "seguranca e triagem; tentativas nao autorizadas podem resultar em moderacao."
            ),
        )
        await self._post_once(
            backup,
            MESSAGES["verification"]["title"],
            description=MESSAGES["verification"]["description"],
            view=VerificationView(),
        )
        await self._post_once(terms, "Termos da loja", description=TERMS_OF_USE)
        await self._post_once(
            attendance,
            "Central de atendimento",
            description="Selecione abaixo o tipo de atendimento desejado.",
            view=TicketTypeSelectView(),
        )
        await self._post_once(
            feedback,
            "Feedback de compradores",
            description="Apenas compradores verificados podem enviar mensagens neste canal.",
        )
        await self._post_once(
            orders,
            "Pedidos",
            description="Acompanhe comunicados e pedidos confirmados da loja.",
        )
        await self._post_once(giveaway, "Sorteios", description="Acompanhe os sorteios ativos neste canal.")
        await self._post_once(warnings, "Avisos", description="Comunicados da equipe de administracao.")
        await self._post_once(restock, "Reposicoes", description="Novas reposicoes serao anunciadas aqui.")
        await self._post_once(
            request_stock,
            "Solicitar reposicao",
            description="Use o botao para avisar a equipe sobre um produto desejado.",
            view=StockRequestView(),
        )
        for channel in product_channels:
            await self._post_once(
                channel,
                "Produtos legais e digitais",
                description="Confira os produtos disponiveis e escolha uma opcao de compra.",
                view=ProductCatalogView(),
            )

        success = Embeds.create_standard(
            title=MESSAGES["server_pre_ready"]["success_title"],
            description=(
                "Estrutura criada com protecao maxima, verificacao, atendimento, loja e Pix. "
                "Cadastre produtos legais com /loja dentro de um canal de produtos."
            ),
        )
        await interaction.followup.send(embed=success, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if message.channel.name != "📥・nao-mande-nada":
            return
        if message.author.id == message.guild.owner_id or message.author.guild_permissions.administrator:
            return

        # Log and Ban (The message stays as per the 'liberated chat' requirement)
        try:
            await message.author.ban(reason="Mensagem em canal reservado de seguranca (Trap)")
        except discord.Forbidden:
            logger.warning("Sem permissao para moderar mensagem no canal reservado de %s", message.guild.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerSetupCog(bot))
