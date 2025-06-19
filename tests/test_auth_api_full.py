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
async def test_auth_register_and_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        token = await create_user_and_token(
            ac,
            "testuser1",
            "test1@example.com",
            "testpass1",
        )

        assert token


@pytest.mark.asyncio
async def test_auth_me_and_preferences():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        token = await create_user_and_token(
            ac,
            "testuser2",
            "test2@example.com",
            "testpass2",
        )

        headers = {"Authorization": f"Bearer {token}"}
        me_resp = await ac.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200

        pref_resp = await ac.put(
            "/api/v1/auth/preferences",
            headers=headers,
            json={"theme": "dark"},
        )

        assert pref_resp.status_code == 200
        assert pref_resp.json()["preferences"]["theme"] == "dark"
