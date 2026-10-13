import aiohttp
import logging
from database.database import AsyncSessionLocal
from database.repositories.verification_repository import VerificationRepository
from config import Config

logger = logging.getLogger('bot.oauth')

class OAuthService:
    def __init__(self, bot):
        self.bot = bot
        # Client ID is the same as Bot ID
        self.client_id = str(bot.user.id) if bot.user else None
        self.client_secret = None # Should be loaded from Config
        self.redirect_uri = "http://localhost:8080/callback" # Default for dev

    async def get_auth_url(self):
        if not self.client_id:
            # Try to get it from bot if not available
            self.client_id = str(self.bot.user.id)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "identify"
        }
        import urllib.parse
        query = urllib.parse.urlencode(params)
        return f"https://discord.com/api/oauth2/authorize?{query}"

    async def handle_callback(self, code: str):
        if not self.client_secret:
            logger.error("OAuth CLIENT_SECRET not configured!")
            return False, "CLIENT_SECRET not configured"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post("https://discord.com/api/oauth2/token", data=data, headers=headers) as resp:
                if resp.status != 200:
                    logger.error(f"OAuth token exchange failed: {await resp.text()}")
                    return False, "Failed to exchange code for token"

                token_data = await resp.json()
                access_token = token_data.get("access_token")

                # Get user info
                headers = {"Authorization": f"Bearer {access_token}"}
                async with session.get("https://discord.com/api/users/@me", headers=headers) as user_resp:
                    if user_resp.status != 200:
                        return False, "Failed to fetch user info"

                    user_info = await user_resp.json()
                    user_id = user_info.get("id")

                    # We need the guild_id to verify them for a specific server.
                    # Since the callback is global, we can't easily know the guild
                    # unless we pass it in the 'state' parameter.
                    return True, user_id

    async def verify_user_in_guild(self, guild_id: int, user_id: str):
        async with AsyncSessionLocal() as session:
            repo = VerificationRepository(session)
            await repo.verify_user(guild_id, user_id)
            return True
