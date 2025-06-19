from httpx import ASGITransport, AsyncClient
import pytest

from main import app


@pytest.mark.asyncio
async def test_auth_me_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_preferences_unauthorized():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.put("/api/v1/auth/preferences", json={"theme": "dark"})

    assert response.status_code == 401
