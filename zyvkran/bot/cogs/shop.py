import uuid
import asyncio
import logging
from typing import Iterable, Optional

import discord
from discord import app_commands
from discord.ext import commands

from database.database import AsyncSessionLocal
from database.repositories.guild_repository import GuildRepository
from database.repositories.order_repository import OrderRepository
from database.repositories.product_repository import ProductRepository
from messages.messages import MESSAGES
from utils.embeds import Embeds
from config import Config

logger = logging.getLogger("bot")


def _staff(member: discord.Member, owner_id: int) -> bool:
    if member.id == owner_id or member.guild_permissions.administrator:
        return True
    return any(
        marker in role.name.lower()
        for role in member.roles
        for marker in ("proprietario", "administrador", "vendedor")
    )


async def _respond(interaction: discord.Interaction, content: str, *, ephemeral: bool = True) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(content, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content, ephemeral=ephemeral)


class ShopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(ProductCatalogView())

    @app_commands.command(name="loja", description="Abre o painel administrativo da loja.")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja(self, interaction: discord.Interaction):
        msg = MESSAGES["shop"]["admin_panel"]
        embed = Embeds.create_standard(title=msg["title"], description=msg["description"])
        await interaction.response.send_message(embed=embed, view=ShopAdminPanelView(), ephemeral=True)

    async def create_purchase_flow(
        self,
        interaction: discord.Interaction,
        product_id: int,
        variant_id: Optional[int] = None,
    ):
        guild = interaction.guild
        if guild is None or not isinstance(interaction.user, discord.Member):
            return await _respond(interaction, "Este recurso so funciona em um servidor.")

        async with AsyncSessionLocal() as session:
            product_repo = ProductRepository(session)
            product = await product_repo.get_product(product_id)
            if product is None or product.guild_id != guild.id or product.status != "active":
                return await _respond(interaction, "Produto indisponivel.")
            if product.stock <= 0:
                return await _respond(interaction, "Produto sem estoque.")

            variants = await product_repo.get_variants_by_product(product_id)
            if variants and variant_id is None:
                return await interaction.response.send_message(
                    "Escolha uma opcao de plano:",
                    view=ProductVariantSelectView(product_id, variants),
                    ephemeral=True,
                )

            amount = product.base_price
            duration = "Padrao"
            if variant_id is not None:
                variant = next((item for item in variants if item.id == variant_id), None)
                if variant is None:
                    return await _respond(interaction, "Opcao de produto invalida.")
                amount = variant.price
                duration = variant.duration

            guild_repo = GuildRepository(session)
            settings = await guild_repo.get_settings(guild.id)
            if settings is None or not settings.pix_key:
                return await _respond(
                    interaction,
                    "A loja ainda nao possui uma chave Pix configurada. Fale com a equipe.",
                )

            order_id = str(uuid.uuid4())[:8].upper()
            order_repo = OrderRepository(session)
            await order_repo.create_order(
                order_id=order_id,
                guild_id=guild.id,
                user_id=str(interaction.user.id),
                product_id=product.id,
                variant_id=variant_id,
                amount=amount,
            )

            category = discord.utils.get(guild.categories, name="Pedidos privados")
            if category is None:
                category = await guild.create_category("Pedidos privados", reason="Fluxo de compra")

            bot_member = guild.me or (self.bot.user and guild.get_member(self.bot.user.id))
            owner = guild.owner or guild.get_member(guild.owner_id)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                ),
            }
            if owner:
                overwrites[owner] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )
            if bot_member:
                overwrites[bot_member] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )
            for role in guild.roles:
                if any(marker in role.name.lower() for marker in ("proprietario", "administrador", "vendedor")):
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=True, read_message_history=True
                    )

            channel = await guild.create_text_channel(
                name=f"pedido-{order_id.lower()}",
                category=category,
                overwrites=overwrites,
                reason=f"Pedido {order_id}",
            )

            flow = MESSAGES["shop"]["purchase_flow"]
            embed = Embeds.create_standard(
                title=flow["order_title"],
                description=flow["order_description"].format(
                    product=product.name,
                    variant=duration,
                    amount=f"{amount:.2f}",
                    pix_key=settings.pix_key,
                ),
                color=0xF1C40F,
            )
            embed.set_footer(text=f"ID do pedido: {order_id}")
            await channel.send(
                embed=embed,
                view=OrderConfirmationView(
                    order_id, product.id, product.name, amount, interaction.user.id
                ),
            )

        await _respond(interaction, f"Pedido criado: {channel.mention}")


class ShopAdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=900)

    @discord.ui.button(label="Produtos", style=discord.ButtonStyle.secondary)
    async def list_products(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as session:
            products = await ProductRepository(session).get_products_by_guild(interaction.guild_id)
        if not products:
            return await interaction.response.send_message("Nenhum produto cadastrado.", ephemeral=True)
        description = "\n".join(
            f"**{product.name}** - R$ {product.base_price:.2f} | estoque: {product.stock}"
            for product in products[:25]
        )
        await interaction.response.send_message(
            embed=Embeds.create_standard(title="Produtos da loja", description=description),
            ephemeral=True,
        )

    @discord.ui.button(label="Criar produto", style=discord.ButtonStyle.green)
    async def create_product(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ProductCreateModal())

    @discord.ui.button(label="Vendas", style=discord.ButtonStyle.secondary)
    async def view_sales(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as session:
            count = await OrderRepository(session).get_confirmed_orders_count(interaction.guild_id)
        await interaction.response.send_message(
            f"Vendas confirmadas: {count}", ephemeral=True
        )


class ProductCreateModal(discord.ui.Modal, title="Criar produto"):
    name = discord.ui.TextInput(label="Nome do produto", placeholder="Ex.: Assinatura mensal")
    description = discord.ui.TextInput(
        label="Descricao publica",
        style=discord.TextStyle.paragraph,
        max_length=800,
    )
    price = discord.ui.TextInput(label="Preco", placeholder="Ex.: 10.00")
    stock = discord.ui.TextInput(label="Estoque", placeholder="Ex.: 50")
    delivery = discord.ui.TextInput(
        label="Entrega apos confirmacao",
        style=discord.TextStyle.paragraph,
        placeholder="Conteudo ou instrucoes legais que o comprador recebera.",
        max_length=1500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            price = float(self.price.value.replace(",", "."))
            stock = int(self.stock.value)
            if price < 0 or stock < 0:
                raise ValueError
        except ValueError:
            return await interaction.response.send_message(
                "Preco e estoque devem ser numeros positivos.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        async with AsyncSessionLocal() as session:
            product = await ProductRepository(session).create_product(
                guild_id=interaction.guild_id,
                name=self.name.value.strip(),
                description=self.description.value.strip(),
                category="Geral",
                base_price=price,
                stock=stock,
                channel_id=str(interaction.channel_id),
                delivery_message=self.delivery.value.strip(),
            )

        embed = Embeds.create_product_embed(
            product.name,
            product.description,
            product.base_price,
            product.stock,
            "Padrao",
        )
        await interaction.channel.send(embed=embed, view=ProductBuyView(product.id))
        await interaction.followup.send(
            f"Produto **{product.name}** criado e publicado neste canal.", ephemeral=True
        )


class ProductCatalogView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Comprar",
        style=discord.ButtonStyle.green,
        custom_id="product_catalog",
    )
    async def select_product(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with AsyncSessionLocal() as session:
            products = await ProductRepository(session).get_active_products_by_channel(
                interaction.guild_id, str(interaction.channel_id)
            )
        if not products:
            return await interaction.response.send_message(
                "Nenhum produto esta disponivel neste canal.", ephemeral=True
            )
        if len(products) == 1:
            cog = interaction.client.get_cog("ShopCog")
            if cog is None:
                return await interaction.response.send_message(
                    "O sistema de compras esta indisponivel.", ephemeral=True
                )
            return await cog.create_purchase_flow(interaction, products[0].id)
        await interaction.response.send_message(
            "Escolha o produto desejado:",
            view=ProductSelectionView(products),
            ephemeral=True,
        )


class ProductBuyView(discord.ui.View):
    def __init__(self, product_id: int):
        super().__init__(timeout=None)
        self.product_id = product_id
        self.children[0].custom_id = f"buy_product:{product_id}"

    @discord.ui.button(label="Comprar", style=discord.ButtonStyle.green)
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("ShopCog")
        if cog is None:
            return await interaction.response.send_message(
                "O sistema de compras esta indisponivel.", ephemeral=True
            )
        await cog.create_purchase_flow(interaction, self.product_id)


class ProductSelection(discord.ui.Select):
    def __init__(self, products: Iterable):
        options = [
            discord.SelectOption(
                label=product.name[:100],
                value=str(product.id),
                description=f"R$ {product.base_price:.2f} | estoque: {product.stock}"[:100],
            )
            for product in list(products)[:25]
        ]
        super().__init__(placeholder="Escolha um produto...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("ShopCog")
        if cog is None:
            return await interaction.response.send_message(
                "O sistema de compras esta indisponivel.", ephemeral=True
            )
        await cog.create_purchase_flow(interaction, int(self.values[0]))


class ProductSelectionView(discord.ui.View):
    def __init__(self, products: Iterable):
        super().__init__(timeout=300)
        self.add_item(ProductSelection(products))


class ProductVariantSelection(discord.ui.Select):
    def __init__(self, product_id: int, variants: Iterable):
        self.product_id = product_id
        options = [
            discord.SelectOption(
                label=variant.name[:100],
                value=str(variant.id),
                description=f"R$ {variant.price:.2f} - {variant.duration}"[:100],
            )
            for variant in list(variants)[:25]
        ]
        super().__init__(placeholder="Escolha o plano...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("ShopCog")
        if cog is None:
            return await interaction.response.send_message(
                "O sistema de compras esta indisponivel.", ephemeral=True
            )
        await cog.create_purchase_flow(interaction, self.product_id, int(self.values[0]))


class ProductVariantSelectView(discord.ui.View):
    def __init__(self, product_id: int, variants: Iterable):
        super().__init__(timeout=300)
        self.add_item(ProductVariantSelection(product_id, variants))


class OrderConfirmationView(discord.ui.View):
    def __init__(
        self,
        order_id: str,
        product_id: int,
        product_name: str,
        amount: float,
        buyer_id: int,
    ):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.product_id = product_id
        self.product_name = product_name
        self.amount = amount
        self.buyer_id = buyer_id

    @discord.ui.button(label="Confirmar pagamento", style=discord.ButtonStyle.green)
    async def confirm_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Este recurso so funciona em um servidor.", ephemeral=True
            )
        if not _staff(interaction.user, guild.owner_id):
            return await interaction.response.send_message(
                MESSAGES["shop"]["purchase_flow"]["no_permission"], ephemeral=True
            )

        async with AsyncSessionLocal() as session:
            order_repo = OrderRepository(session)
            order = await order_repo.get_order(self.order_id)
            if order is None or order.status != "pending":
                return await interaction.response.send_message(
                    "Este pedido ja foi processado.", ephemeral=True
                )

            product_repo = ProductRepository(session)
            product = await product_repo.get_product(order.product_id)
            if product is None or product.stock <= 0:
                return await interaction.response.send_message(
                    "O produto nao possui mais estoque para confirmar este pedido.", ephemeral=True
                )

            await order_repo.update_order_status(
                self.order_id, "confirmed", confirmed_by=str(interaction.user.id)
            )
            await product_repo.update_stock(product.id, -1)

        # 1. Block the channel to prevent further messages
        try:
            await interaction.channel.set_permissions(guild.default_role, send_messages=False)
        except discord.Forbidden:
            pass

        buyer = guild.get_member(self.buyer_id)
        buyer_role = discord.utils.get(guild.roles, name="Comprador")
        if buyer and buyer_role and buyer_role not in buyer.roles:
            try:
                await buyer.add_roles(buyer_role, reason="Compra confirmada")
            except discord.Forbidden:
                pass

        await interaction.response.send_message("Pagamento confirmado e entrega liberada.", ephemeral=True)
        confirmed = MESSAGES["shop"]["confirmed"]
        embed = Embeds.create_standard(
            title=confirmed["title"],
            description=confirmed["description"].format(
                order_id=self.order_id,
                product=self.product_name,
                amount=f"{self.amount:.2f}",
            ),
        )

        # 2. Send Confirmation and Delivery
        await interaction.channel.send(
            content=(
                f"{buyer.mention if buyer else 'Comprador'}, pagamento confirmado.\n"
                f"**Entrega:**\n{product.delivery_message or 'A equipe enviara a entrega neste canal.'}"
            ),
            embed=embed,
        )

        # 3. Send professional DM to buyer
        if buyer:
            try:
                post_purchase = MESSAGES["shop"]["post_purchase"]
                dm_embed = Embeds.create_standard(
                    title=post_purchase["dm_title"],
                    description=post_purchase["dm_description"],
                    color=0x2ECC71
                )
                await buyer.send(embed=dm_embed)
            except discord.Forbidden:
                # Log DM failure
                log_cog = interaction.client.get_cog("LogsCog")
                if log_cog:
                    await log_cog.emit_log(
                        guild,
                        "⚠️ Falha no envio de DM",
                        f"O bot não conseguiu enviar a DM de confirmação para {buyer.mention}.",
                        color=0xFF0000
                    )

        # 4. Request Feedback in the channel
        post_purchase = MESSAGES["shop"]["post_purchase"]
        feedback_embed = Embeds.create_standard(
            title=post_purchase["feedback_title"],
            description=post_purchase["feedback_description"],
            color=Config.BOT_COLOR
        )
        await interaction.channel.send(embed=feedback_embed, view=FeedbackView())

        # Close the channel after a delay
        async def close_channel():
            await interaction.channel.send("O canal será fechado em 30 segundos.")
            logger.info("Aguardando 30s para fechar o canal %s", interaction.channel.name)
            await asyncio.sleep(30)
            try:
                await interaction.channel.delete(reason=f"Pedido {self.order_id} concluido")
                logger.info("Canal %s deletado com sucesso", interaction.channel.name)
            except (discord.NotFound, discord.Forbidden) as e:
                logger.warning("Falha ao deletar canal %s: %s", interaction.channel.name, e)
                pass

        interaction.client.loop.create_task(close_channel())

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Copiar chave Pix", style=discord.ButtonStyle.secondary)
    async def copy_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Use a chave Pix exibida na mensagem do pedido.", ephemeral=True
        )

class FeedbackView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=MESSAGES["shop"]["post_purchase"]["feedback_button"], style=discord.ButtonStyle.secondary)
    async def leave_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # If a specific feedback channel is configured, we guide the user there
        if Config.FEEDBACK_CHANNEL_ID:
            channel = interaction.guild.get_channel(Config.FEEDBACK_CHANNEL_ID)
            if channel:
                await interaction.response.send_message(
                    f"Para deixar seu feedback, por favor utilize o canal {channel.mention}!", ephemeral=True
                )
                return

        await interaction.response.send_message(
            "Por favor, entre em contato com o suporte ou utilize o canal de avaliações do servidor para deixar seu feedback!", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ShopCog(bot))
