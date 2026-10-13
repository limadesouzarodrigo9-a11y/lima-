import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from database.database import AsyncSessionLocal
from database.repositories.guild_repository import GuildRepository
from database.repositories.offense_repository import OffenseRepository
from database.models import SecurityLog
from utils.embeds import Embeds
from config import Config
from messages.messages import MESSAGES

class ProtectionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # (guild_id, user_id) -> [timestamps]
        self.message_history = defaultdict(list)
        self.command_history = defaultdict(list)
        self.interaction_history = defaultdict(list)

    async def get_log_cog(self):
        return self.bot.get_cog("LogsCog")

    async def apply_punishment(self, member: discord.Member, guild: discord.Guild, reason: str):
        """Applies a timeout based on the user's offense history."""
        async with AsyncSessionLocal() as session:
            offense_repo = OffenseRepository(session)
            offense = await offense_repo.increment_offense(guild.id, str(member.id))

            # Punishment escalation: 60s -> 300s -> 3600s (1h)
            timeouts = {1: 60, 2: 300, 3: 3600}
            duration = timeouts.get(offense.severity_level, 3600)

            try:
                await member.timeout(timedelta(seconds=duration), reason=reason)
                punishment_msg = MESSAGES["protection"]["timeout_applied"].format(duration=f"{duration}s")
                # We don't send a public message to avoid further spamming the channel
                # but we can send it in DM if preferred.
            except discord.Forbidden:
                punishment_msg = "Erro: Sem permissão para silenciar usuário."
            except Exception as e:
                punishment_msg = f"Erro ao aplicar punição: {e}"

        # Log the event
        log_cog = await self.get_log_cog()
        if log_cog:
            await log_cog.emit_log(
                guild,
                "⚠️ Spam Detectado",
                f"Usuário {member.mention} silenciado por {duration}s.\nMotivo: {reason}",
                color=0xFFA500,
                fields={"Usuário": member.name, "ID": str(member.id), "Nível": str(offense.severity_level)}
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot or message.webhook_id:
            return

        # 1. Trap Channel Check
        if Config.NO_MESSAGE_CHANNEL_ID and message.channel.id == Config.NO_MESSAGE_CHANNEL_ID:
            try:
                # Capture author and content for logging
                author = message.author
                content = message.content or "Sem conteúdo"
                guild = message.guild

                # Ban the user for sending message in trapped channel (chat liberated: message stays)
                try:
                    await guild.ban(author, reason="Enviou mensagem em canal proibido (Trap)")

                    log_cog = await self.get_log_cog()
                    if log_cog:
                        await log_cog.emit_log(
                            guild,
                            "🔨 Banimento Automático (Trap)",
                            f"Usuário {author.mention} foi banido por enviar mensagem no canal proibido.\nChat liberado: mensagem não foi deletada.",
                            color=0xFF0000,
                            fields={
                                "Usuário": author.name,
                                "ID": str(author.id),
                                "Conteúdo": content[:1024],
                                "Canal": message.channel.mention,
                                "Motivo": "Mensagem em canal Trap"
                            }
                        )
                except discord.Forbidden:
                    log_cog = await self.get_log_cog()
                    if log_cog:
                        await log_cog.emit_log(
                            guild,
                            "❌ Erro de Permissão",
                            f"O bot não possui permissão para banir {author.mention} no canal Trap.",
                            color=0xFF0000
                        )
                except Exception as e:
                    log_cog = await self.get_log_cog()
                    if log_cog:
                        await log_cog.emit_log(
                            guild,
                            "❌ Erro no Banimento",
                            f"Falha ao banir {author.mention} no canal Trap: {e}",
                            color=0xFF0000
                        )
                return  # Skip spam detection for trap channel to avoid double punishment
            except Exception as e:
                # Handle unexpected errors in early processing
                log_cog = await self.get_log_cog()
                if log_cog:
                    await log_cog.emit_log(
                        message.guild,
                        "❌ Erro Inesperado (Trap)",
                        f"Falha ao processar mensagem no canal Trap: {e}",
                        color=0xFF0000
                    )
                return

        # 2. Anti-Spam (Message Rate Limit)
        now = datetime.utcnow()
        user_key = (message.guild.id, message.author.id)

        # Clean and update history
        self.message_history[user_key] = [ts for ts in self.message_history[user_key] if (now - ts).total_seconds() < Config.TIME_WINDOW]
        self.message_history[user_key].append(now)

        if len(self.message_history[user_key]) > Config.MAX_MESSAGES:
            try:
                await message.delete()
            except discord.NotFound:
                pass

            await self.apply_punishment(message.author, message.guild, "Excesso de mensagens (Spam)")
            return

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # This is a simple way to handle cooldowns if we use @commands.cooldown
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⚠️ Comando em cooldown! Aguarde {error.retry_after:.2f}s.", delete_after=5)

    # --- Interaction/Command Protection ---
    # Since most commands are Slash Commands (app_commands),
    # we need a way to wrap them or use a check.
    # I'll implement a global interaction check.

async def setup(bot):
    await bot.add_cog(ProtectionCog(bot))
