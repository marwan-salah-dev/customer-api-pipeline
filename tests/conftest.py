import os
import pytest
from app.db import get_connection


@pytest.fixture(autouse=True)
def clean_table():
    url = os.environ["DATABASE_URL"]
    assert url.endswith("_test"), "Tests must run against a database ending in _test"
    with get_connection() as conn:
        conn.execute("TRUNCATE customers RESTART IDENTITY")
    yield