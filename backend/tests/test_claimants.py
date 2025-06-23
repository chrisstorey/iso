# This is the test_claimants.py file for claimant-related tests.
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
# from typing import Optional # Not needed for these tests yet

# app.main and models are imported by conftest or via fixtures
from app.models import Claimant as ClaimantModel
# from app.schemas import ClaimantCreate, Claimant as ClaimantSchema # For direct schema use if needed

# Test functions will now receive 'test_app_client' and 'db_session_for_direct_use' as arguments from conftest.py

def test_create_claimant(test_app_client: TestClient, db_session_for_direct_use: Session):
    claimant_data = {
        "name": "John Doe",
        "home_latitude": 51.5074,
        "home_longitude": 0.1278
    }
    response = test_app_client.post("/claimants/", json=claimant_data)

    print(f"Create claimant response status: {response.status_code}")
    try:
        print(f"Create claimant response JSON: {response.json()}")
    except Exception as e:
        print(f"Create claimant response text: {response.text}")
        print(f"Error decoding JSON: {e}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert data["name"] == claimant_data["name"]
    assert data["home_latitude"] == claimant_data["home_latitude"]
    assert data["home_longitude"] == claimant_data["home_longitude"]
    assert "id" in data
    assert "travel_extent_geojson" in data
    assert data["travel_extent_geojson"] is not None
    assert data["travel_extent_geojson"]["type"] == "Polygon" # From Shapely's mapping()
    assert len(data["travel_extent_geojson"]["coordinates"][0]) > 3 # A polygon has multiple points

    # Verify it's in the database using the provided db_session_for_direct_use
    db_claimant = db_session_for_direct_use.query(ClaimantModel).filter(ClaimantModel.id == data["id"]).first()
    assert db_claimant is not None
    assert db_claimant.name == claimant_data["name"]

def test_read_claimants_empty(test_app_client: TestClient): # No direct db use needed
    response = test_app_client.get("/claimants/")
    assert response.status_code == 200
    assert response.json() == []

def test_read_claimants_after_creation(test_app_client: TestClient): # No direct db use needed for setup
    claimant_data1 = {"name": "Jane Smith", "home_latitude": 52.0, "home_longitude": -1.0}
    resp1 = test_app_client.post("/claimants/", json=claimant_data1)
    assert resp1.status_code == 200

    claimant_data2 = {"name": "Peter Jones", "home_latitude": 53.0, "home_longitude": 0.5}
    resp2 = test_app_client.post("/claimants/", json=claimant_data2)
    assert resp2.status_code == 200

    response = test_app_client.get("/claimants/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    names_in_response = {c["name"] for c in data}
    assert claimant_data1["name"] in names_in_response
    assert claimant_data2["name"] in names_in_response

def test_read_single_claimant(test_app_client: TestClient, db_session_for_direct_use: Session):
    claimant_data = {
        "name": "Specific Claimant",
        "home_latitude": 50.0,
        "home_longitude": 0.0
    }
    create_resp = test_app_client.post("/claimants/", json=claimant_data)
    assert create_resp.status_code == 200
    created_claimant_id = create_resp.json()["id"]

    response = test_app_client.get(f"/claimants/{created_claimant_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == claimant_data["name"]
    assert data["id"] == created_claimant_id
    assert data["travel_extent_geojson"] is not None # Default extent is created

def test_read_non_existent_claimant(test_app_client: TestClient):
    response = test_app_client.get("/claimants/99999")
    assert response.status_code == 404

def test_update_claimant_details(test_app_client: TestClient, db_session_for_direct_use: Session):
    claimant_data = {"name": "Original Name", "home_latitude": 10.0, "home_longitude": 10.0}
    create_resp = test_app_client.post("/claimants/", json=claimant_data)
    assert create_resp.status_code == 200
    created_claimant = create_resp.json()
    claimant_id = created_claimant["id"]
    original_extent = created_claimant["travel_extent_geojson"]

    update_payload = {"name": "Updated Name", "home_latitude": 12.0, "home_longitude": 12.0}
    response = test_app_client.patch(f"/claimants/{claimant_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["home_latitude"] == 12.0
    assert data["home_longitude"] == 12.0
    assert data["travel_extent_geojson"] is not None
    assert data["travel_extent_geojson"] != original_extent # Extent should have been recalculated

    # Check DB
    db_claimant = db_session_for_direct_use.query(ClaimantModel).filter(ClaimantModel.id == claimant_id).first()
    assert db_claimant.name == "Updated Name"
    assert db_claimant.travel_extent_geojson != original_extent

def test_update_claimant_name_only(test_app_client: TestClient, db_session_for_direct_use: Session):
    claimant_data = {"name": "Name Only Original", "home_latitude": 20.0, "home_longitude": 20.0}
    create_resp = test_app_client.post("/claimants/", json=claimant_data)
    assert create_resp.status_code == 200
    created_claimant = create_resp.json()
    claimant_id = created_claimant["id"]
    original_extent = created_claimant["travel_extent_geojson"]
    original_lat = created_claimant["home_latitude"]
    original_lon = created_claimant["home_longitude"]

    update_payload = {"name": "Name Only Updated"}
    response = test_app_client.patch(f"/claimants/{claimant_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Name Only Updated"
    assert data["home_latitude"] == original_lat # Should not change
    assert data["home_longitude"] == original_lon # Should not change
    assert data["travel_extent_geojson"] == original_extent # Extent should NOT be recalculated

def test_delete_claimant(test_app_client: TestClient, db_session_for_direct_use: Session):
    claimant_data = {"name": "To Be Deleted", "home_latitude": 30.0, "home_longitude": 30.0}
    create_resp = test_app_client.post("/claimants/", json=claimant_data)
    assert create_resp.status_code == 200
    claimant_id = create_resp.json()["id"]

    delete_resp = test_app_client.delete(f"/claimants/{claimant_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["id"] == claimant_id

    # Verify gone from DB
    db_claimant = db_session_for_direct_use.query(ClaimantModel).filter(ClaimantModel.id == claimant_id).first()
    assert db_claimant is None

def test_delete_non_existent_claimant(test_app_client: TestClient):
    response = test_app_client.delete("/claimants/99999")
    assert response.status_code == 404
