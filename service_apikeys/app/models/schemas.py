'''
======================================================================
File: schemas.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from datetime import datetime
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
