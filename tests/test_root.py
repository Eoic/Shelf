from httpx import ASGITransport, AsyncClient
import pytest

from main import app


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "links" in data
    assert "documentation" in data["links"]
    assert "redoc" in data["links"]
    assert "minio" in data["links"]
