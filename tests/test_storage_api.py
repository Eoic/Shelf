from httpx import ASGITransport, AsyncClient
import pytest

from main import app


@pytest.mark.asyncio
async def test_storage_list_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/storage/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_storage_get_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/storage/some-id")

    assert response.status_code == 401
