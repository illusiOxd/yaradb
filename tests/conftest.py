import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from starlette.testclient import TestClient
from main import app
from core.constants.main_values import STORAGE_FILE, WAL_FILE


@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """Clean database before each test"""
    if os.path.exists(STORAGE_FILE):
        os.remove(STORAGE_FILE)
    if os.path.exists(WAL_FILE):
        os.remove(WAL_FILE)

    yield

    if os.path.exists(STORAGE_FILE):
        os.remove(STORAGE_FILE)
    if os.path.exists(WAL_FILE):
        os.remove(WAL_FILE)


@pytest.fixture(scope="function")
def client():
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client
