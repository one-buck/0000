'''
======================================================================
File: dependencies.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.

    Commits on success, rolls back on exception.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise