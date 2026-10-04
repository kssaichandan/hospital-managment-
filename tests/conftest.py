"""Shared PyTest fixtures. Every test gets a brand-new, empty database file."""
import os
import sys

import pytest

# Make the project folder importable (app.py, database.py, validators.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from database import HospitalDB  # noqa: E402


@pytest.fixture
def db(tmp_path):
    return HospitalDB(str(tmp_path / "test.db"))


@pytest.fixture
def app(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    client.post("/", data={"username": "admin", "password": "admin123"})
    return client
