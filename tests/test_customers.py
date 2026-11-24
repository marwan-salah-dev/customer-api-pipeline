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


def test_list_customers():
    client.post("/customers", json={"name": "Ali Hassan", "email": "ali@example.com"})
    response = client.get("/customers")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "ali@example.com"


def test_deactivate_hides_customer_from_list():
    ali = client.post("/customers", json={"name": "Ali Hassan", "email": "ali@example.com"}).json()
    client.post("/customers", json={"name": "Mara", "email": "mara@example.com"})

    response = client.post(f"/customers/{ali['id']}/deactivate")
    assert response.status_code == 200
    assert response.json()["active"] is False

    listed = client.get("/customers").json()
    assert len(listed) == 1
    assert listed[0]["email"] == "mara@example.com"


def test_activate_brings_customer_back():
    ali = client.post("/customers", json={"name": "Ali Hassan", "email": "ali@example.com"}).json()
    client.post(f"/customers/{ali['id']}/deactivate")

    response = client.post(f"/customers/{ali['id']}/activate")
    assert response.json()["active"] is True
    assert len(client.get("/customers").json()) == 1


def test_deactivate_unknown_customer_returns_404():
    response = client.post("/customers/999/deactivate")
    assert response.status_code == 404