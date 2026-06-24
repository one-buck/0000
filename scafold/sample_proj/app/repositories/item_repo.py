'''
======================================================================
File: item_repo.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.entities import Base, Item

engine = create_async_engine(settings.DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class ItemRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert(self, data: dict) -> Item:
        item = Item(**data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def find_by_id(self, item_id: int) -> Item | None:
        result = await self.session.execute(select(Item).where(Item.id == item_id))
        return result.scalar_one_or_none()


async def get_item_repo() -> ItemRepo:
    async with async_session() as session:
        yield ItemRepo(session=session)
