'''
======================================================================
File: items.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import ItemCreate, ItemResponse


router = APIRouter()

@router.post("/", response_model=ItemResponse, status_code=201)
async def create_item(data: ItemCreate):
    return {
    "id": 0,
    "name": data.name,
    "description": data.description,
    "created_at": "2024-07-15T10:30:00"
}


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int):
    return {
    "id": item_id,
    "name": "Wireless Mouse",
    "description": "A sleek ergonomic mouse with Bluetooth support",
    "created_at": "2024-07-15T10:30:00"
}

