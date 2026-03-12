from fastapi.testclient import TestClient

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the ERP System API"}

def test_create_inventory_item(client: TestClient):
    data = {
        "sku": "TEST-SKU-001",
        "name": "Test Item",
        "description": "A test inventory item",
        "quantity": 100,
        "min_quantity": 10,
        "unit_price": 50.5,
        "category": "General"
    }
    response = client.post("/api/v1/inventory/items", json=data)
    assert response.status_code == 200
    item = response.json()
    assert item["sku"] == data["sku"]
    assert item["name"] == data["name"]
    assert item["id"] is not None

def test_create_project(client: TestClient):
    data = {
        "title": "Solar Installation X",
        "customer_name": "Customer A",
        "status": "DRAFT",
        "total_value": 10000.0
    }
    response = client.post("/api/v1/projects", json=data)
    assert response.status_code == 200
    project = response.json()
    assert project["title"] == data["title"]
    assert project["customer_name"] == data["customer_name"]
    assert project["status"] == "DRAFT"

def test_create_shipment_and_incident(client: TestClient):
    # 1. Create Shipment
    shipment_data = {
        "tracking_number": "TRK-001",
        "origin": "Port A",
        "destination": "Warehouse B",
        "status": "PENDING",
        "total_cost": 500.0
    }
    response = client.post("/api/v1/logistics/", json=shipment_data)
    assert response.status_code == 200
    shipment = response.json()
    assert shipment["tracking_number"] == "TRK-001"
    
    # 2. Report Incident
    incident_data = {
        "shipment_id": shipment["id"],
        "description": "Customs Delay",
        "incident_type": "Delay"
    }
    response = client.post("/api/v1/logistics/incidents", json=incident_data)
    assert response.status_code == 200
    incident = response.json()
    assert incident["description"] == incident_data["description"]

def test_kpi_leaderboard(client: TestClient):
    response = client.get("/api/v1/kpi/leaderboard")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
