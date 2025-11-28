import pytest
from datetime import datetime
from main import app


@pytest.fixture(autouse=True)
def disable_rate_limit():
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    yield
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = True


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
    response = client.request("DELETE", "/system/self-destruct", json={
        "verification_phrase": "BDaray",
        "safety_pin": datetime.now().year + 1,
        "confirm": True
    })
    assert response.status_code == 200

    list_resp = client.get("/table/list")
    assert len(list_resp.json()) == 0


def test_create_hash_index(client):
    table_name = "index_test_users"

    for i in range(5):
        client.post("/document/create", json={
            "table_name": table_name,
            "body": {"email": f"user{i}@example.com", "age": 20 + i}
        })

    response = client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })
    assert response.status_code == 200
    assert response.json()["field"] == "email"
    assert response.json()["index_type"] == "hash"

    list_resp = client.get(f"/table/{table_name}/indexes")
    assert list_resp.status_code == 200
    indexes = list_resp.json()["indexes"]
    assert len(indexes) == 1
    assert indexes[0]["field"] == "email"
    assert indexes[0]["type"] == "hash"


def test_hash_index_speeds_up_search(client):
    table_name = "performance_test"

    for i in range(10):
        client.post("/document/create", json={
            "table_name": table_name,
            "name": f"doc_{i}",
            "body": {"email": f"user{i}@example.com", "status": "active"}
        })

    client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })

    response = client.post("/document/find", json={
        "email": "user5@example.com"
    }, params={"table_name": table_name})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["body"]["email"] == "user5@example.com"


def test_index_updates_on_document_update(client):
    table_name = "index_update_test"

    create_resp = client.post("/document/create", json={
        "table_name": table_name,
        "name": "doc_update",
        "body": {"email": "old@example.com", "status": "pending"}
    })
    doc_id = create_resp.json()["_id"]

    client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })

    client.put(f"/document/update/{doc_id}", json={
        "version": 1,
        "body": {"email": "new@example.com", "status": "active"}
    })

    response = client.post("/document/find", json={
        "email": "new@example.com"
    }, params={"table_name": table_name})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1

    response_old = client.post("/document/find", json={
        "email": "old@example.com"
    }, params={"table_name": table_name})

    assert len(response_old.json()) == 0


def test_find_with_sort_and_pagination(client):
    table_name = "pagination_test"

    for i in range(20):
        client.post("/document/create", json={
            "table_name": table_name,
            "name": f"item_{i}",
            "body": {"name": f"Item {i}", "order": i}
        })

    response = client.post("/document/find", json={}, params={
        "table_name": table_name,
        "sort_by": "order",
        "order": "asc",
        "limit": 5,
        "offset": 0
    })

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 5
    assert results[0]["body"]["order"] == 0
    assert results[4]["body"]["order"] == 4

    response_page2 = client.post("/document/find", json={}, params={
        "table_name": table_name,
        "sort_by": "order",
        "order": "asc",
        "limit": 5,
        "offset": 5
    })

    results_page2 = response_page2.json()
    assert len(results_page2) == 5
    assert results_page2[0]["body"]["order"] == 5


def test_find_with_descending_sort(client):
    table_name = "sort_desc_test"

    for i in range(5):
        client.post("/document/create", json={
            "table_name": table_name,
            "name": f"val_{i}",
            "body": {"value": i * 10}
        })

    response = client.post("/document/find", json={}, params={
        "table_name": table_name,
        "sort_by": "value",
        "order": "desc"
    })

    results = response.json()
    assert results[0]["body"]["value"] == 40
    assert results[-1]["body"]["value"] == 0


def test_create_btree_index(client):
    table_name = "btree_test"

    for i in range(10):
        client.post("/document/create", json={
            "table_name": table_name,
            "body": {"name": f"Product {i}", "price": 10 * (i + 1)}
        })

    response = client.post(f"/table/{table_name}/index/create", json={
        "field": "price",
        "index_type": "btree"
    })
    assert response.status_code == 200
    assert response.json()["index_type"] == "btree"


def test_drop_index(client):
    table_name = "drop_index_test"

    client.post("/document/create", json={
        "table_name": table_name,
        "body": {"email": "test@example.com"}
    })

    client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })

    list_resp = client.get(f"/table/{table_name}/indexes")
    assert len(list_resp.json()["indexes"]) == 1

    drop_resp = client.delete(f"/table/{table_name}/index/email")
    assert drop_resp.status_code == 200

    list_resp = client.get(f"/table/{table_name}/indexes")
    assert len(list_resp.json()["indexes"]) == 0


def test_index_on_nonexistent_table(client):
    response = client.post("/table/nonexistent/index/create", json={
        "field": "email",
        "index_type": "hash"
    })
    assert response.status_code == 404


def test_duplicate_index_creation(client):
    table_name = "duplicate_index_test"

    client.post("/document/create", json={
        "table_name": table_name,
        "body": {"email": "test@example.com"}
    })

    resp1 = client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })
    assert resp1.status_code == 200

    resp2 = client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })
    assert resp2.status_code == 400


def test_multiple_indexes_on_table(client):
    table_name = "multi_index_test"

    for i in range(5):
        client.post("/document/create", json={
            "table_name": table_name,
            "body": {
                "email": f"user{i}@example.com",
                "age": 20 + i,
                "status": "active"
            }
        })

    client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })

    client.post(f"/table/{table_name}/index/create", json={
        "field": "age",
        "index_type": "btree"
    })

    client.post(f"/table/{table_name}/index/create", json={
        "field": "status",
        "index_type": "hash"
    })

    list_resp = client.get(f"/table/{table_name}/indexes")
    indexes = list_resp.json()["indexes"]
    assert len(indexes) == 3
def test_index_updates_on_document_update(client):
    table_name = "index_update_test"

    create_resp = client.post("/document/create", json={
        "table_name": table_name,
        "name": "doc_update",
        "body": {"email": "old@example.com", "status": "pending"}
    })
    doc_id = create_resp.json()["_id"]

    client.post(f"/table/{table_name}/index/create", json={
        "field": "email",
        "index_type": "hash"
    })

    client.put(f"/document/update/{doc_id}", json={
        "version": 1,
        "body": {"email": "new@example.com", "status": "active"}
    })

    response = client.post("/document/find", json={
        "email": "new@example.com"
    }, params={"table_name": table_name})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1

    response_old = client.post("/document/find", json={
        "email": "old@example.com"
    }, params={"table_name": table_name})

    assert len(response_old.json()) == 0


def test_find_with_sort_and_pagination(client):
    table_name = "pagination_test"

    for i in range(20):
        client.post("/document/create", json={
            "table_name": table_name,
            "name": f"item_{i}",
            "body": {"name": f"Item {i}", "order": i}
        })

    response = client.post("/document/find", json={}, params={
        "table_name": table_name,
        "sort_by": "order",
        "order": "asc",
        "limit": 5,
        "offset": 0
    })

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 5
    assert results[0]["body"]["order"] == 0
    assert results[4]["body"]["order"] == 4

    response_page2 = client.post("/document/find", json={}, params={
        "table_name": table_name,
        "sort_by": "order",
        "order": "asc",
        "limit": 5,
        "offset": 5
    })

    results_page2 = response_page2.json()
    assert len(results_page2) == 5
    assert results_page2[0]["body"]["order"] == 5


def test_find_with_descending_sort(client):
    table_name = "sort_desc_test"

    for i in range(5):
        client.post("/document/create", json={
            "table_name": table_name,
            "name": f"val_{i}",
            "body": {"value": i * 10}
        })

    response = client.post("/document/find", json={}, params={
        "table_name": table_name,
        "sort_by": "value",
        "order": "desc"
    })

    results = response.json()
    assert results[0]["body"]["value"] == 40
    assert results[-1]["body"]["value"] == 0