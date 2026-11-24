from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg

from app.db import get_connection

app = FastAPI(title="Customer API")


class CustomerIn(BaseModel):
    name: str
    email: str
    phone: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/customers", status_code=201)
def add_customer(customer: CustomerIn):
    try:
        with get_connection() as conn:
            row = conn.execute(
                "INSERT INTO customers (name, email, phone) "
                "VALUES (%s, %s, %s) "
                "RETURNING id, name, email, phone, active, created_at",
                (customer.name, customer.email, customer.phone),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already exists")
    return row


@app.get("/customers")
def list_customers():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, email, phone, active, created_at "
            "FROM customers WHERE active = TRUE ORDER BY id"
        ).fetchall()
    return rows


def set_active(customer_id: int, active: bool):
    with get_connection() as conn:
        row = conn.execute(
            "UPDATE customers SET active = %s, updated_at = now() "
            "WHERE id = %s "
            "RETURNING id, name, email, phone, active, created_at, updated_at",
            (active, customer_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return row


@app.post("/customers/{customer_id}/deactivate")
def deactivate_customer(customer_id: int):
    return set_active(customer_id, False)


@app.post("/customers/{customer_id}/activate")
def activate_customer(customer_id: int):
    return set_active(customer_id, True)