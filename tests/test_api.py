import pytest
from datetime import datetime

TEST_TABLE = "test_table"


def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_create_and_get_document(client):
    response = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test_user",
        "body": {"username": "alice"}
    })
    assert response.status_code == 200
    doc_id = response.json()["_id"]

    response = client.get(f"/document/get/{doc_id}")
    assert response.status_code == 200
    assert response.json()["body"]["username"] == "alice"


def test_optimistic_locking(client):
    create_resp = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test", "body": {"counter": 1}
    })
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["_id"]

    resp = client.put(f"/document/update/{doc_id}", json={
        "version": 1, "body": {"counter": 2}
    })
    assert resp.status_code == 200

    resp = client.put(f"/document/update/{doc_id}", json={
        "version": 1, "body": {"counter": 3}
    })
    assert resp.status_code == 409


def test_find_documents(client):
    client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test_user",
        "body": {"username": "bob", "level": 5}
    })
    client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test_user",
        "body": {"username": "charlie", "level": 5}
    })

    response = client.post("/document/find", json={"level": 5})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2


def test_archive_document(client):
    response = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test", "body": {"data": "test"}
    })
    doc_id = response.json()["_id"]

    response = client.put(f"/document/archive/{doc_id}")
    assert response.status_code == 200
    assert response.json()["archived_at"] is not None

    response = client.get(f"/document/get/{doc_id}")
    assert response.status_code == 404


def test_archive_already_archived(client):
    response = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test", "body": {"data": "test"}
    })
    doc_id = response.json()["_id"]
    client.put(f"/document/archive/{doc_id}")

    response = client.put(f"/document/archive/{doc_id}")
    assert response.status_code == 404


def test_find_with_archived(client):
    response = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test_user",
        "body": {"username": "archived_user", "status": "deleted"}
    })
    doc_id = response.json()["_id"]
    client.put(f"/document/archive/{doc_id}")

    response = client.post("/document/find", json={"status": "deleted"})
    assert response.status_code == 200
    assert len(response.json()) == 0

    response = client.post("/document/find?include_archived=true", json={"status": "deleted"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_nonexistent_document(client):
    response = client.get("/document/get/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_nonexistent_document(client):
    response = client.put("/document/update/00000000-0000-0000-0000-000000000000", json={
        "version": 1,
        "body": {"data": "test"}
    })
    assert response.status_code == 404


def test_update_archived_document(client):
    response = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test", "body": {"data": "test"}
    })
    doc_id = response.json()["_id"]
    client.put(f"/document/archive/{doc_id}")

    response = client.put(f"/document/update/{doc_id}", json={
        "version": 2,
        "body": {"data": "updated"}
    })
    assert response.status_code == 404


def test_body_hash_integrity(client):
    response = client.post("/document/create", json={
        "table_name": TEST_TABLE,
        "name": "test",
        "body": {"key": "value"}
    })
    assert response.status_code == 200
    doc = response.json()
    assert "body_hash" in doc
    assert len(doc["body_hash"]) == 64


def test_create_strict_table_and_validate_schema(client):
    table_name = "strict_users"

    response = client.post("/table/create", json={
        "name": table_name,
        "mode": "strict",
        "schema_definition": {
            "type": "object",
            "required": ["username", "age"],
            "properties": {
                "username": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
    })
    assert response.status_code == 200
    assert response.json()["mode"] == "strict"

    resp_valid = client.post("/document/create", json={
        "table_name": table_name,
        "name": "user_ok",
        "body": {"username": "alice", "age": 25}
    })
    assert resp_valid.status_code == 200

    resp_invalid = client.post("/document/create", json={
        "table_name": table_name,
        "name": "user_bad",
        "body": {"username": "bob", "age": 30, "city": "London"}
    })
    assert resp_invalid.status_code == 400


def test_unique_constraints(client):
    table_name = "unique_users"

    client.post("/table/create", json={
        "name": table_name,
        "mode": "free",
        "unique_fields": ["email"]
    })

    resp1 = client.post("/document/create", json={
        "table_name": table_name,
        "name": "user1",
        "body": {"email": "test@example.com", "name": "Test 1"}
    })
    assert resp1.status_code == 200

    resp2 = client.post("/document/create", json={
        "table_name": table_name,
        "name": "user2",
        "body": {"email": "test@example.com", "name": "Imposter"}
    })
    assert resp2.status_code == 400

    resp3 = client.post("/document/create", json={
        "table_name": table_name,
        "name": "user3",
        "body": {"email": "other@example.com"}
    })
    assert resp3.status_code == 200


def test_read_only_table(client):
    table_name = "archive_2020"

    client.post("/table/create", json={
        "name": table_name,
        "read_only": True
    })

    response = client.post("/document/create", json={
        "table_name": table_name,
        "name": "doc1",
        "body": {"data": "should fail"}
    })

    assert response.status_code == 400


def test_lazy_table_creation(client):
    table_name = "auto_created_table"

    response = client.post("/document/create", json={
        "table_name": table_name,
        "name": "auto_doc",
        "body": {"any": "field"}
    })

    assert response.status_code == 200

    list_resp = client.get("/table/list")
    tables = list_resp.json()
    assert any(t["name"] == table_name for t in tables)


def test_delete_table(client):
    table_name = "temp_table"

    client.post("/document/create", json={
        "table_name": table_name,
        "body": {"x": 1}
    })

    del_resp = client.delete(f"/table/{table_name}")
    assert del_resp.status_code == 200

    list_resp = client.get("/table/list")
    assert not any(t["name"] == table_name for t in list_resp.json())


def test_self_destruct(client):
    response = client.delete("/system/self-destruct", json={
        "verification_phrase": "BDaray",
        "safety_pin": datetime.now().year + 1,
        "confirm": True
    })
    assert response.status_code == 200

    list_resp = client.get("/table/list")
    assert len(list_resp.json()) == 0