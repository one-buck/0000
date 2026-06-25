'''
======================================================================
File: __init__.py
Author: Z Name, 
Created: 2026-06-25
======================================================================
'''

from fastapi import APIRouter

from app.routes.items import router as items_router


router = APIRouter()

router.include_router(items_router, prefix="/items", tags=["items"])

