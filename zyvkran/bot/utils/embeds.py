import discord
from config import Config

class Embeds:
    @staticmethod
    def create_standard(title: str, description: str, color=Config.BOT_COLOR, footer=None, thumbnail=None):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        if footer:
            embed.set_footer(text=footer)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        return embed

    @staticmethod
    def create_product_embed(product_name: str, description: str, price: float, stock: int, duration: str, image_url: str = None):
        from messages.messages import MESSAGES
        msg = MESSAGES["shop"]["product_embed"]

        embed = discord.Embed(
            title=msg["title"].format(product_name=product_name),
            description=msg["description"].format(
                description=description,
                price=f"{price:.2f}",
                stock=stock,
                duration=duration
            ),
            color=Config.BOT_COLOR
        )
        if image_url:
            embed.set_image(url=image_url)
        return embed
