from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def get_entity_or_404(db: AsyncSession, model, id: int, detail: str = "Not found"):
    result = await db.execute(select(model).where(model.id == id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=detail)
    return entity
