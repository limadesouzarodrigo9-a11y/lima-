from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, ProductVariant

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(self, guild_id: int, name: str, description: str, category: str, base_price: float, stock: int, channel_id: str, delivery_message: str = None):
        product = Product(
            guild_id=guild_id,
            name=name,
            description=description,
            category=category,
            base_price=base_price,
            stock=stock,
            channel_id=channel_id,
            delivery_message=delivery_message
        )
        self.session.add(product)
        await self.session.commit()
        return product

    async def get_products_by_guild(self, guild_id: int):
        result = await self.session.execute(select(Product).filter(Product.guild_id == guild_id))
        return result.scalars().all()

    async def get_active_products_by_channel(self, guild_id: int, channel_id: str):
        result = await self.session.execute(
            select(Product).filter(
                Product.guild_id == guild_id,
                Product.channel_id == channel_id,
                Product.status == "active",
                Product.stock > 0
            )
        )
        return result.scalars().all()

    async def get_product(self, product_id: int):
        result = await self.session.execute(select(Product).filter(Product.id == product_id))
        return result.scalar_one_or_none()

    async def update_product(self, product_id: int, **kwargs):
        product = await self.get_product(product_id)
        if product:
            for key, value in kwargs.items():
                setattr(product, key, value)
            await self.session.commit()
        return product

    async def delete_product(self, product_id: int):
        product = await self.get_product(product_id)
        if product:
            await self.session.delete(product)
            await self.session.commit()
            return True
        return False

    async def create_variant(self, product_id: int, name: str, price: float, duration: str):
        variant = ProductVariant(
            product_id=product_id,
            name=name,
            price=price,
            duration=duration
        )
        self.session.add(variant)
        await self.session.commit()
        return variant

    async def get_variants_by_product(self, product_id: int):
        result = await self.session.execute(select(ProductVariant).filter(ProductVariant.product_id == product_id))
        return result.scalars().all()

    async def delete_variant(self, variant_id: int):
        result = await self.session.execute(select(ProductVariant).filter(ProductVariant.id == variant_id))
        variant = result.scalar_one_or_none()
        if variant:
            await self.session.delete(variant)
            await self.session.commit()
            return True
        return False

    async def update_stock(self, product_id: int, amount: int):
        product = await self.get_product(product_id)
        if product:
            await self.session.refresh(product)
            product.stock += amount
            await self.session.commit()
        return product
