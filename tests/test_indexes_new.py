import pytest
from core.constants.main_values import STORAGE_FILE, WAL_FILE
import os


def test_full_index_lifecycle(client):
    table_name = "indexed_users"

    client.post("/table/create", json={"name": table_name})

    resp = client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })
    assert resp.status_code == 200
    assert resp.json()["index_type"] == "hash"

    client.post("/document/create", json={
        "table_name": table_name,
        "body": {"email": "test@example.com", "name": "Test User"}
    })
    client.post("/document/create", json={
        "table_name": table_name,
        "body": {"email": "other@example.com", "name": "Other User"}
    })

    search_resp = client.post("/document/find", json={"email": "test@example.com"}, params={"table_name": table_name})
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) == 1
    assert results[0]["body"]["email"] == "test@example.com"

    list_resp = client.get(f"/table/{table_name}/indexes")
    assert list_resp.status_code == 200
    indexes = list_resp.json()["indexes"]
    assert len(indexes) == 1
    assert indexes[0]["field"] == "email"

    del_resp = client.delete(f"/table/{table_name}/index/email")
    assert del_resp.status_code == 200

    list_resp_after = client.get(f"/table/{table_name}/indexes")
    assert len(list_resp_after.json()["indexes"]) == 0

    search_resp_scan = client.post("/document/find", json={"email": "test@example.com"},
                                   params={"table_name": table_name})
    assert len(search_resp_scan.json()) == 1


def test_archive_removes_from_index(client):
    table_name = "archive_test"
    client.post("/table/create", json={"name": table_name})
    client.post(f"/table/{table_name}/index/create", json={"field": "status", "index_type": "hash"})

    create_resp = client.post("/document/create", json={
        "table_name": table_name,
        "body": {"status": "active", "data": 123}
    })
    doc_id = create_resp.json()["_id"]

    find_1 = client.post("/document/find", json={"status": "active"}, params={"table_name": table_name})
    assert len(find_1.json()) == 1

    client.put(f"/document/archive/{doc_id}")

    find_2 = client.post("/document/find", json={"status": "active"}, params={"table_name": table_name})
    assert len(find_2.json()) == 0


def test_delete_table_cleans_indexes(client):
    table_name = "temp_table"
    client.post("/table/create", json={"name": table_name})
    client.post(f"/table/{table_name}/index/create", json={"field": "x", "index_type": "hash"})

    client.delete(f"/table/{table_name}")

    resp = client.get(f"/table/{table_name}/indexes")
    assert resp.status_code == 404