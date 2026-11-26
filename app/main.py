"""Customer API.

A small REST API that manages customers in a PostgreSQL database. It is the
sample application delivered by the CI/CD pipeline in .github/workflows/ci.yml.

Endpoints:
    GET  /health                           liveness + database check (used by the pipeline)
    POST /customers                        add a customer
    GET  /customers                        list active customers
    PUT  /customers/{id}                   update a customer
    POST /customers/{id}/deactivate        soft delete (row is kept, marked inactive)
    POST /customers/{id}/activate          undo a deactivate

Notes:
    - SQL is written by hand (no ORM) and values are always passed as query
      parameters (%s), never formatted into the SQL string, to prevent SQL injection.
    - "Delete" is a soft delete: rows are never removed, so nothing is lost.
    - Status codes: 201 created, 404 unknown id, 409 email already used,
      422 request body invalid (raised by FastAPI), 503 database unreachable.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg

from app.db import get_connection

app = FastAPI(title="Customer API")


class CustomerIn(BaseModel):
    """Request body for creating or updating a customer.

    FastAPI validates incoming JSON against this model and returns 422
    automatically if a required field is missing or has the wrong type.
    """

    name: str
    email: str
    phone: str | None = None


@app.get("/health")
def health():
    """Return 200 if the app is running and can reach its database, else 503.

    The pipeline calls this after every deploy, so a deploy only counts as
    successful when the app actually works, not just when the files arrived.
    """
    try:
        with get_connection() as conn:
            # Cheapest possible query: proves the database answers, touches no table.
            conn.execute("SELECT 1")
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok"}


@app.post("/customers", status_code=201)
def add_customer(customer: CustomerIn):
    """Add a customer. Returns 409 if the email is already used."""
    try:
        with get_connection() as conn:
            # RETURNING sends the new row back in the same round trip.
            row = conn.execute(
                "INSERT INTO customers (name, email, phone) "
                "VALUES (%s, %s, %s) "
                "RETURNING id, name, email, phone, active, created_at",
                (customer.name, customer.email, customer.phone),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        # The UNIQUE constraint on email (db/schema.sql) enforces this, so two
        # requests at the same moment still cannot create a duplicate.
        raise HTTPException(status_code=409, detail="Email already exists")
    return row


@app.get("/customers")
def list_customers():
    """List active customers, oldest first. Deactivated customers are hidden."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, email, phone, active, created_at "
            "FROM customers WHERE active = TRUE ORDER BY id"
        ).fetchall()
    return rows


def set_active(customer_id: int, active: bool):
    """Shared helper for activate and deactivate. Returns 404 if the id is unknown."""
    with get_connection() as conn:
        row = conn.execute(
            "UPDATE customers SET active = %s, updated_at = now() "
            "WHERE id = %s "
            "RETURNING id, name, email, phone, active, created_at, updated_at",
            (active, customer_id),
        ).fetchone()
    # No row returned means no customer had that id.
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return row


@app.post("/customers/{customer_id}/deactivate")
def deactivate_customer(customer_id: int):
    """Soft delete: mark the customer inactive. The row stays in the table."""
    return set_active(customer_id, False)


@app.post("/customers/{customer_id}/activate")
def activate_customer(customer_id: int):
    """Undo a deactivate."""
    return set_active(customer_id, True)


@app.put("/customers/{customer_id}")
def update_customer(customer_id: int, customer: CustomerIn):
    """Replace a customer's details. 404 if the id is unknown, 409 if the new email is taken."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "UPDATE customers SET name = %s, email = %s, phone = %s, updated_at = now() "
                "WHERE id = %s "
                "RETURNING id, name, email, phone, active, created_at, updated_at",
                (customer.name, customer.email, customer.phone, customer_id),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already exists")
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return row
