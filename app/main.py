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
    return {
        "id": row[0], "name": row[1], "email": row[2],
        "phone": row[3], "active": row[4], "created_at": row[5],
    }