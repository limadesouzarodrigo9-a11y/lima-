import discord
from discord.ext import commands
import asyncio
import logging
import os

from config import Config

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('bot')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=Config.DEFAULT_PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # Initialize Database
        from database.database import init_db
        await init_db()
        logger.info('Database initialized')

        # Load Cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded extension: {filename}')
                except Exception as e:
                    logger.error(f'Failed to load extension {filename}: {e}')

        # Sync Slash Commands
        try:
            synced = await self.tree.sync()
            logger.info(f'Synced {len(synced)} command(s)')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        await self.change_presence(activity=discord.Game(name="Bot Profissional | /despertar"))

async def main():
    bot = MyBot()
    async with bot:
        try:
            await bot.start(Config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
