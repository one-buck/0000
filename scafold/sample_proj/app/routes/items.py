'''
======================================================================
File: items.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ItemCreate, ItemResponse
from app.services.item_service import ItemService, get_item_service

router = APIRouter()


@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(
    data: ItemCreate,
    svc: ItemService = Depends(get_item_service),
):
    return await svc.create(data)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    svc: ItemService = Depends(get_item_service),
):
    item = await svc.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
