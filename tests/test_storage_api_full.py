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
async def test_storage_crud():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        token = await create_user_and_token(
            ac,
            "storageuser",
            "storage@example.com",
            "storagepass",
        )

        headers = {"Authorization": f"Bearer {token}"}
        payload = {"storage_type": "FILE_SYSTEM", "config": {}}
        create_resp = await ac.post("/api/v1/storage/", headers=headers, json=payload)
        assert create_resp.status_code == 201

        storage_id = create_resp.json()["id"]
        get_resp = await ac.get(f"/api/v1/storage/{storage_id}", headers=headers)
        assert get_resp.status_code == 200

        list_resp = await ac.get("/api/v1/storage/", headers=headers)
        assert list_resp.status_code == 200
        assert any(s["id"] == storage_id for s in list_resp.json()["items"])

        update_resp = await ac.put(
            f"/api/v1/storage/{storage_id}",
            headers=headers,
            json={"config": {}},
        )
        assert update_resp.status_code == 200

        default_resp = await ac.put(
            f"/api/v1/storage/{storage_id}/set-default",
            headers=headers,
        )
        assert default_resp.status_code == 200

        del_resp = await ac.delete(f"/api/v1/storage/{storage_id}", headers=headers)
        assert del_resp.status_code == 204
