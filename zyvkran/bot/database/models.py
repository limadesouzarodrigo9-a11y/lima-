from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base

class Guild(Base):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True) # Discord Guild ID
    owner_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    settings = relationship("GuildSettings", back_populates="guild", uselist=False)
    products = relationship("Product", back_populates="guild")

class GuildSettings(Base):
    __tablename__ = 'guild_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'), unique=True)

    server_name = Column(String)
    currency = Column(String, default="BRL") # BRL, USD
    protection_level = Column(String, default="green") # green, orange, red
    pix_key = Column(String)
    pix_type = Column(String) # CPF, Email, Phone, Random
    shop_channel_id = Column(String) # Discord Channel ID where the shop catalog is posted
    trap_channels = Column(Text) # Comma-separated list of channel IDs that ban on message

    guild = relationship("Guild", back_populates="settings")

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))

    name = Column(String)
    description = Column(Text)
    category = Column(String)
    base_price = Column(Float)
    stock = Column(Integer, default=0)
    status = Column(String, default="active") # active, inactive
    image_url = Column(String, nullable=True)
    channel_id = Column(String) # Discord Channel ID where product is displayed
    delivery_message = Column(Text, nullable=True) # Sent only in the buyer's private order channel

    guild = relationship("Guild", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")

class ProductVariant(Base):
    __tablename__ = 'product_variants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'))

    name = Column(String) # e.g., "1 Month"
    price = Column(Float)
    duration = Column(String) # e.g., "30 days"

    product = relationship("Product", back_populates="variants")

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, unique=True) # Unique order string
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(String)
    product_id = Column(Integer, ForeignKey('products.id'))
    variant_id = Column(Integer, ForeignKey('product_variants.id'))

    amount = Column(Float)
    status = Column(String, default="pending") # pending, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String, nullable=True)

class Ticket(Base):
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(String)
    channel_id = Column(String)
    category = Column(String) # Support, Purchase, etc.
    status = Column(String, default="open") # open, closed
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

class SecurityLog(Base):
    __tablename__ = 'security_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(String)
    action = Column(String)
    details = Column(Text)
    severity = Column(String) # low, medium, high
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserOffense(Base):
    __tablename__ = 'user_offenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(String)
    offense_count = Column(Integer, default=0)
    last_offense_at = Column(DateTime, default=datetime.utcnow)
    severity_level = Column(Integer, default=1) # 1: low, 2: medium, 3: high

class Verification(Base):

    __tablename__ = 'verifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(String)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
