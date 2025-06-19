from httpx import ASGITransport, AsyncClient
import pytest

from main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/health")

    assert response.status_code == 404
