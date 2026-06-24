'''
======================================================================
File: item_service.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''from fastapi import Depends

from app.logger import get_logger
from app.models.schemas import ItemCreate, ItemResponse
from app.repositories.item_repo import ItemRepo, get_item_repo

logger = get_logger(__name__)


class ItemService:
    def __init__(self, repo: ItemRepo):
        self.repo = repo

    async def create(self, data: ItemCreate) -> ItemResponse:
        logger.info(f"Creating item: {data.name}")
        item = await self.repo.insert(data.model_dump())
        return ItemResponse.model_validate(item)

    async def get(self, item_id: int) -> ItemResponse | None:
        item = await self.repo.find_by_id(item_id)
        if item:
            return ItemResponse.model_validate(item)
        return None


def get_item_service(repo: ItemRepo = Depends(get_item_repo)) -> ItemService:
    return ItemService(repo=repo)
