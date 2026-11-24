from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_add_customer():
    response = client.post(
        "/customers",
        json={"name": "Ali Hassan", "email": "ali@example.com", "phone": "555-0101"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ali Hassan"
    assert body["email"] == "ali@example.com"
    assert body["active"] is True


def test_duplicate_email_is_rejected():
    customer = {"name": "Ali Hassan", "email": "ali@example.com"}
    client.post("/customers", json=customer)
    response = client.post("/customers", json=customer)
    assert response.status_code == 409


def test_missing_name_is_rejected():
    response = client.post("/customers", json={"email": "ali@example.com"})
    assert response.status_code == 422