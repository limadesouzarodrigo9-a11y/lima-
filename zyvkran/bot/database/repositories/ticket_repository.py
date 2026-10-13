from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Ticket

class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(self, guild_id: int, user_id: str, channel_id: str, category: str):
        ticket = Ticket(
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            category=category
        )
        self.session.add(ticket)
        await self.session.commit()
        return ticket

    async def get_ticket_by_channel(self, channel_id: str):
        result = await self.session.execute(select(Ticket).filter(Ticket.channel_id == channel_id))
        return result.scalar_one_or_none()

    async def get_open_tickets_count(self, guild_id: int, user_id: str):
        result = await self.session.execute(
            select(func.count(Ticket.id)).filter(
                Ticket.guild_id == guild_id,
                Ticket.user_id == user_id,
                Ticket.status == "open"
            )
        )
        return result.scalar()

    async def close_ticket(self, ticket_id: int):
        from datetime import datetime
        result = await self.session.execute(select(Ticket).filter(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.status = "closed"
            ticket.closed_at = datetime.utcnow()
            await self.session.commit()
        return ticket
