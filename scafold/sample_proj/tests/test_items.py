'''
======================================================================
File: test_items.py
Author: Your Name
Created: 2026-06-24 15:51:07
======================================================================

'''import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
