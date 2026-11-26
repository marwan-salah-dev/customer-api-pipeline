"""Shared test setup, run automatically by pytest before every test."""

import os
import pytest
from app.db import get_connection


@pytest.fixture(autouse=True)
def clean_table():
    """Start every test with an empty customers table.

    Safety check: refuse to run unless DATABASE_URL points at a database whose
    name ends in _test, so the tests can never wipe a real database.
    """
    url = os.environ["DATABASE_URL"]
    assert url.endswith("_test"), "Tests must run against a database ending in _test"
    with get_connection() as conn:
        # RESTART IDENTITY resets the id counter so every test starts from id 1.
        conn.execute("TRUNCATE customers RESTART IDENTITY")
    yield
