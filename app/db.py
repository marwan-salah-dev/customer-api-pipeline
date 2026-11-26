"""Database connection helper."""

import os
import psycopg
from psycopg.rows import dict_row


def get_connection():
    """Open a connection to the database in the DATABASE_URL environment variable.

    The connection string comes from the environment, not the code, so the same
    code runs on a laptop, in CI and in each Azure environment with no secret in
    the repo. Rows come back as dictionaries so FastAPI can return them as JSON.
    Use it in a `with` block: the transaction is committed when the block ends
    without an error, rolled back otherwise, and the connection is closed.
    """
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
