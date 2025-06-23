# This is the test_services.py file for service-related tests.
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Optional

from app.models import Service
# from app.schemas import ServiceCreate # Not strictly needed if using helper

# Helper to create a service directly in DB for testing GET filters
# This now takes the db_session fixture from conftest.py
def _create_service_in_db(db: Session, name: str, description: Optional[str], category: Optional[str], fees: Optional[str], location_json: Optional[dict] = None):
    service = Service(
        name=name,
        description=description,
        category=category,
        fees=fees,
        location=location_json # Store as JSON if LocationType is JSON (handled by model's conditional type)
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

# Test functions will now receive 'test_app_client' and 'db_session_for_direct_use' as arguments from conftest.py

def test_read_services_empty(test_app_client: TestClient): # No direct db use here
    # manage_tables fixture from conftest ensures tables are created and empty
    response = test_app_client.get("/services/")
    assert response.status_code == 200
    assert response.json() == []

def test_create_and_read_service(test_app_client: TestClient, db_session_for_direct_use: Session):
    # db_session_for_direct_use is the session from conftest.
    try:
        # Service with location data
        _create_service_in_db(
            db_session_for_direct_use,
            name="Test Service 1 with Location",
            description="Description 1",
            category="GeoTest",
            fees="Free",
            location_json={"type": "Point", "coordinates": [-0.09, 51.505]} # Lon, Lat for Leaflet
        )
        # Service without location data
        _create_service_in_db(
                db_session_for_direct_use,
            name="Test Service 2 no Location",
            description="Description 2",
            category="NoGeo",
            fees="Paid"
        )
    except Exception as e:
        pytest.fail(f"Error creating service in DB: {e}")


    response = test_app_client.get("/services/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    service1_found = any(s["name"] == "Test Service 1 with Location" for s in data)
    service2_found = any(s["name"] == "Test Service 2 no Location" for s in data)
    assert service1_found
    assert service2_found

    for s in data:
        if s["name"] == "Test Service 1 with Location":
            assert s["location"] == {"type": "Point", "coordinates": [-0.09, 51.505]}
        if s["name"] == "Test Service 2 no Location":
            assert s["location"] is None


def test_filter_services_by_category(test_app_client: TestClient, db_session_for_direct_use: Session):
    _create_service_in_db(db_session_for_direct_use, name="Health Service 1", description="Desc1", category="Health", fees="Free")
    _create_service_in_db(db_session_for_direct_use, name="Education Service 1", description="Desc2", category="Education", fees="Paid")
    _create_service_in_db(db_session_for_direct_use, name="Health Service 2", description="Desc3", category="Health", fees="Low Cost")

    response = test_app_client.get("/services/?category=Health")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Health Service 1" # Order might depend on insertion/DB
    assert data[1]["name"] == "Health Service 2"
    for service_in_response in data:
        assert "Health" in service_in_response["category"]

    response = test_app_client.get("/services/?category=Edu") # Partial match
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Education Service 1"

def test_filter_services_by_fees(test_app_client: TestClient, db_session_for_direct_use: Session):
    _create_service_in_db(db_session_for_direct_use, name="Service A", description="DescA", category="General", fees="Free")
    _create_service_in_db(db_session_for_direct_use, name="Service B", description="DescB", category="Specific", fees="Low Cost")
    _create_service_in_db(db_session_for_direct_use, name="Service C", description="DescC", category="General", fees="Free Tier Available")

    response = test_app_client.get("/services/?fees=Free")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Names can be in any order
    names = {s['name'] for s in data}
    assert "Service A" in names
    assert "Service C" in names


    response = test_app_client.get("/services/?fees=Low")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Service B"

def test_filter_services_by_category_and_fees(test_app_client: TestClient, db_session_for_direct_use: Session):
    _create_service_in_db(db_session_for_direct_use, name="Health Free", description="D1", category="Health", fees="Free")
    _create_service_in_db(db_session_for_direct_use, name="Health Paid", description="D2", category="Health", fees="Paid")
    _create_service_in_db(db_session_for_direct_use, name="Support Free", description="D3", category="Support", fees="Free")

    response = test_app_client.get("/services/?category=Health&fees=Free")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Health Free"

    response = test_app_client.get("/services/?category=Support&fees=Paid") # No match
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

# Tests for US6: /services/within/claimant/{claimant_id}
def test_get_services_within_claimant_area_not_found(test_app_client: TestClient):
    response = test_app_client.get("/services/within/claimant/9999") # Non-existent claimant
    assert response.status_code == 404
    assert response.json()["detail"] == "Claimant not found"

def test_get_services_within_claimant_area_no_extent(test_app_client: TestClient, db_session_for_direct_use: Session):
    # Create a claimant directly, ensuring travel_extent_geojson is None
    from app.models import Claimant as ClaimantModel
    claimant = ClaimantModel(name="No Extent Claimant", home_latitude=0, home_longitude=0, travel_extent_geojson=None)
    db_session_for_direct_use.add(claimant)
    db_session_for_direct_use.commit()
    db_session_for_direct_use.refresh(claimant)

    response = test_app_client.get(f"/services/within/claimant/{claimant.id}")
    assert response.status_code == 400 # As per current main.py logic
    assert response.json()["detail"] == "Claimant does not have a defined travel extent"


def test_get_services_within_claimant_area_test_mode_empty(test_app_client: TestClient, db_session_for_direct_use: Session):
    # Create a claimant with a (dummy) travel extent
    # In test mode, USE_GEOMETRY is false, so get_services_within_geojson returns []
    # from app.models import Claimant as ClaimantModel # Not needed directly
    # from app.crud import create_circular_buffer_geojson # Not needed directly

    # We need to use the actual claimant creation logic from crud to get the extent generated
    # Or manually create one that looks like it.
    # For this test, let's simulate a claimant with an extent.
    # The actual extent data doesn't matter much here as the spatial query is skipped.

    # Create claimant using the app's endpoint to ensure travel_extent is generated
    claimant_data = {"name": "Extent Claimant", "home_latitude": 51.5, "home_longitude": -0.1}
    create_claimant_response = test_app_client.post("/claimants/", json=claimant_data) # This uses its own session via override
    assert create_claimant_response.status_code == 200
    created_claimant = create_claimant_response.json()
    claimant_id = created_claimant["id"]

    # Create some services (their locations don't matter for this specific test case in JSON mode)
    _create_service_in_db(db_session_for_direct_use, name="Service Alpha", description="D_A", category="C1", fees="F1", location_json={"type": "Point", "coordinates": [-0.1, 51.5]})
    _create_service_in_db(db_session_for_direct_use, name="Service Beta", description="D_B", category="C2", fees="F2", location_json={"type": "Point", "coordinates": [0.0, 51.6]})

    response = test_app_client.get(f"/services/within/claimant/{claimant_id}")
    assert response.status_code == 200
    # Because USE_GEOMETRY is False in testing, crud.get_services_within_geojson returns []
    assert response.json() == []

# Tests for US7: POST /services/
def test_create_new_service_no_location(test_app_client: TestClient, db_session_for_direct_use: Session):
    service_data = {
        "name": "Awesome New Service",
        "description": "This is a great service.",
        "category": "Community",
        "fees": "Free",
        "url": "http://example.com/awesome",
        "email": "contact@example.com"
    }
    response = test_app_client.post("/services/", json=service_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == service_data["name"]
    assert data["description"] == service_data["description"]
    assert data["category"] == service_data["category"]
    assert data["location"] is None # No lat/lon provided

    # Verify in DB
    service_in_db = db_session_for_direct_use.query(Service).filter(Service.id == data["id"]).first()
    assert service_in_db is not None
    assert service_in_db.name == service_data["name"]
    assert service_in_db.location is None

def test_create_new_service_with_location(test_app_client: TestClient, db_session_for_direct_use: Session):
    service_data = {
        "name": "Located Service",
        "description": "Found at a place.",
        "category": "Local",
        "latitude": 51.500,
        "longitude": -0.100
    }
    response = test_app_client.post("/services/", json=service_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == service_data["name"]
    assert data["location"] is not None
    # In test mode (USE_GEOMETRY=False), location is stored as JSON: {"type": "Point", "coordinates": [lon, lat]}
    assert data["location"]["type"] == "Point"
    assert data["location"]["coordinates"] == [-0.100, 51.500]

    # Verify in DB
    service_in_db = db_session_for_direct_use.query(Service).filter(Service.id == data["id"]).first()
    assert service_in_db is not None
    assert service_in_db.name == service_data["name"]
    assert service_in_db.location is not None
    assert service_in_db.location["type"] == "Point"
    assert service_in_db.location["coordinates"] == [-0.100, 51.500]

def test_create_new_service_invalid_data(test_app_client: TestClient):
    # Missing required 'name' field
    service_data_invalid = {
        "description": "A service without a name.",
        "category": "Problem"
    }
    response = test_app_client.post("/services/", json=service_data_invalid)
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error

# Tests for US8: PATCH /services/{service_id}
def test_update_service(test_app_client: TestClient, db_session_for_direct_use: Session):
    # First, create a service to update
    initial_service_data = {
        "name": "Initial Service Name",
        "description": "Initial Description",
        "category": "Old Category",
        "latitude": 50.0,
        "longitude": 0.0
    }
    response = test_app_client.post("/services/", json=initial_service_data)
    assert response.status_code == 201
    created_service = response.json()
    service_id = created_service["id"]

    # Data for partial update
    update_payload = {
        "name": "Updated Service Name",
        "fees": "£5",
        "latitude": 50.1, # Also update location
        "longitude": 0.1
    }
    response = test_app_client.patch(f"/services/{service_id}", json=update_payload)
    assert response.status_code == 200
    updated_data = response.json()

    assert updated_data["id"] == service_id
    assert updated_data["name"] == "Updated Service Name"
    assert updated_data["description"] == "Initial Description" # Should not change
    assert updated_data["category"] == "Old Category" # Should not change
    assert updated_data["fees"] == "£5" # New field added
    assert updated_data["location"]["coordinates"] == [0.1, 50.1] # Location updated

    # Verify in DB
    service_in_db = db_session_for_direct_use.query(Service).filter(Service.id == service_id).first()
    assert service_in_db.name == "Updated Service Name"
    assert service_in_db.fees == "£5"
    assert service_in_db.location["coordinates"] == [0.1, 50.1]

def test_update_service_clear_location(test_app_client: TestClient, db_session_for_direct_use: Session):
    initial_service_data = {
        "name": "Service to Clear Location",
        "latitude": 50.0,
        "longitude": 0.0
    }
    response = test_app_client.post("/services/", json=initial_service_data)
    assert response.status_code == 201
    created_service = response.json()
    service_id = created_service["id"]
    assert created_service["location"] is not None

    update_payload = {
        "latitude": None, # Signal to clear location
        "longitude": None
    }
    response = test_app_client.patch(f"/services/{service_id}", json=update_payload)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["location"] is None

    service_in_db = db_session_for_direct_use.query(Service).filter(Service.id == service_id).first()
    assert service_in_db.location is None


def test_update_non_existent_service(test_app_client: TestClient):
    update_payload = {"name": "Trying to update nothing"}
    response = test_app_client.patch("/services/99999", json=update_payload)
    assert response.status_code == 404

# Tests for US9: DELETE /services/{service_id}
def test_delete_service(test_app_client: TestClient, db_session_for_direct_use: Session):
    # Create a service to delete
    service_data = {
        "name": "Service to be Deleted",
        "description": "Temporary service.",
        "category": "DeletionTest"
    }
    create_response = test_app_client.post("/services/", json=service_data)
    assert create_response.status_code == 201
    created_service = create_response.json()
    service_id = created_service["id"]

    # Delete the service
    delete_response = test_app_client.delete(f"/services/{service_id}")
    assert delete_response.status_code == 200
    deleted_data = delete_response.json()
    assert deleted_data["id"] == service_id
    assert deleted_data["name"] == service_data["name"]

    # Verify it's gone from the DB
    service_in_db = db_session_for_direct_use.query(Service).filter(Service.id == service_id).first()
    assert service_in_db is None

    # Try to get it via API - should be 404 (this depends on if GET /services/{id} is implemented)
    # get_response = test_app_client.get(f"/services/{service_id}")
    # assert get_response.status_code == 404
    # For now, we check the DB. GET single service is not yet implemented.

def test_delete_non_existent_service(test_app_client: TestClient):
    response = test_app_client.delete("/services/99999")
    assert response.status_code == 404
