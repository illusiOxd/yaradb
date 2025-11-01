import pytest


def test_ping(client):
    """Test basic ping endpoint"""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_create_and_get_document(client):
    """Test document creation and retrieval"""
    response = client.post("/document/create", json={
        "name": "test_user",
        "body": {"username": "alice"}
    })
    assert response.status_code == 200
    doc_id = response.json()["_id"]

    response = client.get(f"/document/get/{doc_id}")
    assert response.status_code == 200
    assert response.json()["body"]["username"] == "alice"


def test_optimistic_locking(client):
    """Test optimistic concurrency control"""
    create_resp = client.post("/document/create", json={
        "name": "test", "body": {"counter": 1}
    })
    doc_id = create_resp.json()["_id"]

    # First update should succeed
    resp = client.put(f"/document/update/{doc_id}", json={
        "version": 1, "body": {"counter": 2}
    })
    assert resp.status_code == 200

    # Second update with old version should fail
    resp = client.put(f"/document/update/{doc_id}", json={
        "version": 1, "body": {"counter": 3}
    })
    assert resp.status_code == 409


def test_find_documents(client):
    """Test document search"""
    # Create test documents
    client.post("/document/create", json={
        "name": "test_user",
        "body": {"username": "bob", "level": 5}
    })
    client.post("/document/create", json={
        "name": "test_user",
        "body": {"username": "charlie", "level": 5}
    })

    # Find documents with level 5
    response = client.post("/document/find", json={"level": 5})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2


def test_archive_document(client):
    """Test document archiving"""
    # Create document
    response = client.post("/document/create", json={
        "name": "test", "body": {"data": "test"}
    })
    doc_id = response.json()["_id"]

    # Archive it
    response = client.put(f"/document/archive/{doc_id}")
    assert response.status_code == 200
    assert response.json()["archived_at"] is not None

    # Try to get it (should not be found)
    response = client.get(f"/document/get/{doc_id}")
    assert response.status_code == 404


def test_archive_already_archived(client):
    """Test archiving an already archived document"""
    # Create and archive
    response = client.post("/document/create", json={
        "name": "test", "body": {"data": "test"}
    })
    doc_id = response.json()["_id"]
    client.put(f"/document/archive/{doc_id}")

    # Try to archive again
    response = client.put(f"/document/archive/{doc_id}")
    assert response.status_code == 404  # Not found (archived docs are hidden)


def test_find_with_archived(client):
    """Test finding documents including archived ones"""
    # Create and archive a document
    response = client.post("/document/create", json={
        "name": "test_user",
        "body": {"username": "archived_user", "status": "deleted"}
    })
    doc_id = response.json()["_id"]
    client.put(f"/document/archive/{doc_id}")

    # Find without archived (should find 0)
    response = client.post("/document/find", json={"status": "deleted"})
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Find with archived (should find 1)
    response = client.post("/document/find?include_archived=true", json={"status": "deleted"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_nonexistent_document(client):
    """Test getting a document that doesn't exist"""
    response = client.get("/document/get/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_nonexistent_document(client):
    """Test updating a document that doesn't exist"""
    response = client.put("/document/update/00000000-0000-0000-0000-000000000000", json={
        "version": 1,
        "body": {"data": "test"}
    })
    assert response.status_code == 404


def test_update_archived_document(client):
    """Test updating an archived document"""
    # Create and archive
    response = client.post("/document/create", json={
        "name": "test", "body": {"data": "test"}
    })
    doc_id = response.json()["_id"]
    client.put(f"/document/archive/{doc_id}")

    # Try to update (should fail - document is hidden when archived)
    response = client.put(f"/document/update/{doc_id}", json={
        "version": 2,
        "body": {"data": "updated"}
    })
    assert response.status_code == 404


def test_body_hash_integrity(client):
    """Test that body_hash is calculated correctly"""
    response = client.post("/document/create", json={
        "name": "test",
        "body": {"key": "value"}
    })
    assert response.status_code == 200
    doc = response.json()
    assert "body_hash" in doc
    assert len(doc["body_hash"]) == 64  # SHA-256 hash length