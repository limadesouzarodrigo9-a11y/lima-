from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Order
from datetime import datetime

class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(self, order_id: str, guild_id: int, user_id: str, product_id: int, variant_id: int, amount: float):
        order = Order(
            order_id=order_id,
            guild_id=guild_id,
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            amount=amount
        )
        self.session.add(order)
        await self.session.commit()
        return order

    async def get_order(self, order_id: str):
        result = await self.session.execute(select(Order).filter(Order.order_id == order_id))
        return result.scalar_one_or_none()

    async def update_order_status(self, order_id: str, status: str, confirmed_by: str = None):
        result = await self.session.execute(select(Order).filter(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = status
            if confirmed_by:
                order.confirmed_by = confirmed_by
                order.confirmed_at = datetime.utcnow()
            await self.session.commit()
        return order

    async def get_orders_by_guild(self, guild_id: int):
        result = await self.session.execute(select(Order).filter(Order.guild_id == guild_id))
        return result.scalars().all()

    async def get_confirmed_orders_count(self, guild_id: int):
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(Order.id)).filter(Order.guild_id == guild_id, Order.status == "confirmed")
        )
        return result.scalar()
