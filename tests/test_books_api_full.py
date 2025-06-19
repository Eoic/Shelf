from httpx import ASGITransport, AsyncClient
import pytest

from main import app

REGISTER_URL = "/api/v1/auth/register"
TOKEN_URL = "/api/v1/auth/token"


@pytest.mark.asyncio
async def create_user_and_token(ac, username, email, password):
    reg_resp = await ac.post(
        REGISTER_URL,
        json={"username": username, "email": email, "password": password},
    )
    assert reg_resp.status_code == 200

    token_resp = await ac.post(
        TOKEN_URL,
        data={"username": username, "password": password},
    )
    assert token_resp.status_code == 200

    token = token_resp.json()["access_token"]
    return token


@pytest.mark.asyncio
async def test_books_list_and_crud():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        token = await create_user_and_token(
            ac,
            "bookuser",
            "book@example.com",
            "bookpass",
        )

        headers = {"Authorization": f"Bearer {token}"}
        list_resp = await ac.get("/api/v1/books/", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

        get_resp = await ac.get("/api/v1/books/nonexistent", headers=headers)
        assert get_resp.status_code == 404
