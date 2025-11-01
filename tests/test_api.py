import pytest
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
async def test_create_and_get_document():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/document/create", json={
            "name": "test_user",
            "body": {"username": "alice"}
        })
        assert response.status_code == 200
        doc_id = response.json()["_id"]

        response = await client.get(f"/document/get/{doc_id}")
        assert response.status_code == 200
        assert response.json()["body"]["username"] == "alice"


@pytest.mark.asyncio
async def test_optimistic_locking():
    async with AsyncClient(app=app, base_url="http://test") as client:
        create_resp = await client.post("/document/create", json={
            "name": "test", "body": {"counter": 1}
        })
        doc_id = create_resp.json()["_id"]

        resp = await client.put(f"/document/update/{doc_id}", json={
            "version": 1, "body": {"counter": 2}
        })
        assert resp.status_code == 200

        resp = await client.put(f"/document/update/{doc_id}", json={
            "version": 1, "body": {"counter": 3}
        })
        assert resp.status_code == 409
