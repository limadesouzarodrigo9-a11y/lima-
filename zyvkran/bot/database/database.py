from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import Config

# Async Engine
engine = create_async_engine(
    Config.DATABASE_URL,
    echo=False,
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def init_db():
    """Initializes the database by creating all tables."""
    # Import all models here to ensure they are registered with Base.metadata
    from database import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # SQLite does not evolve existing tables with create_all. Keep the small
        # local schema compatible with installations created before delivery support.
        if engine.url.get_backend_name() == "sqlite":
            # Update products table
            columns_prod = await conn.execute(text("PRAGMA table_info(products)"))
            names_prod = {row[1] for row in columns_prod}
            if "delivery_message" not in names_prod:
                await conn.execute(text("ALTER TABLE products ADD COLUMN delivery_message TEXT"))

            # Update guild_settings table
            columns_settings = await conn.execute(text("PRAGMA table_info(guild_settings)"))
            names_settings = {row[1] for row in columns_settings}
            if "shop_channel_id" not in names_settings:
                await conn.execute(text("ALTER TABLE guild_settings ADD COLUMN shop_channel_id TEXT"))
            if "trap_channels" not in names_settings:
                await conn.execute(text("ALTER TABLE guild_settings ADD COLUMN trap_channels TEXT"))
