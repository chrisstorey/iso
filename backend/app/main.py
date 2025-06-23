# This is the main.py file for the FastAPI application.
from fastapi import FastAPI, Depends, HTTPException # Add HTTPException
from sqlalchemy.orm import Session
from . import crud, models, schemas # Add schemas
from .database import SessionLocal, engine, get_db # Add get_db

import os # Import os

# Create database tables on startup
# In a production environment, you would typically use Alembic migrations for this.
# Only run create_all if not in testing mode, as tests will manage their own DB creation.
if not (os.getenv("TESTING", "false").lower() == "true"):
    models.Base.metadata.create_all(bind=engine)


app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Open Referral UK Service Finder API"}

from typing import Optional # Import Optional

# US1: View a list of all available services
# US2: Filter services by category, location, and cost
@app.get("/services/", response_model=list[schemas.Service])
def read_services(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    fees: Optional[str] = None,
    # Add location query params here e.g.
    # min_lat: Optional[float] = None, max_lat: Optional[float] = None,
    # min_lon: Optional[float] = None, max_lon: Optional[float] = None,
    db: Session = Depends(get_db)
):
    services = crud.get_services(
        db,
        skip=skip,
        limit=limit,
        category=category,
        fees=fees
        # Pass location params to crud.get_services
        # min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon
    )
    return services

# US7: Add new services to the directory
@app.post("/services/", response_model=schemas.Service, status_code=201)
def create_new_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    # The crud.create_service function now handles lat/lon from ServiceCreate
    return crud.create_service(db=db, service=service)

# US8: Edit or update existing service information
@app.patch("/services/{service_id}", response_model=schemas.Service)
def update_existing_service(service_id: int, service: schemas.ServiceUpdate, db: Session = Depends(get_db)):
    updated_service = crud.update_service(db=db, service_id=service_id, service_update=service)
    if updated_service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated_service

# US9: Remove services that are no longer available
@app.delete("/services/{service_id}", response_model=schemas.Service) # Or return a 204 No Content with a simple message
def remove_service(service_id: int, db: Session = Depends(get_db)):
    deleted_service = crud.delete_service(db=db, service_id=service_id)
    if deleted_service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return deleted_service # Return the deleted service object as confirmation

# US4: Add new claimants to the system
@app.post("/claimants/", response_model=schemas.Claimant)
def create_new_claimant(claimant: schemas.ClaimantCreate, db: Session = Depends(get_db)):
    return crud.create_claimant(db=db, claimant=claimant)

# Placeholder for US10 - Get Claimants (will be expanded)
@app.get("/claimants/", response_model=list[schemas.Claimant])
def read_all_claimants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    claimants = crud.get_claimants(db, skip=skip, limit=limit)
    return claimants

@app.get("/claimants/{claimant_id}", response_model=schemas.Claimant)
def read_single_claimant(claimant_id: int, db: Session = Depends(get_db)):
    db_claimant = crud.get_claimant(db, claimant_id=claimant_id)
    if db_claimant is None:
        raise HTTPException(status_code=404, detail="Claimant not found")
    return db_claimant

@app.patch("/claimants/{claimant_id}", response_model=schemas.Claimant)
def update_existing_claimant(claimant_id: int, claimant: schemas.ClaimantUpdate, db: Session = Depends(get_db)):
    updated_claimant = crud.update_claimant(db=db, claimant_id=claimant_id, claimant_update=claimant)
    if updated_claimant is None:
        raise HTTPException(status_code=404, detail="Claimant not found")
    return updated_claimant

@app.delete("/claimants/{claimant_id}", response_model=schemas.Claimant)
def remove_claimant(claimant_id: int, db: Session = Depends(get_db)):
    deleted_claimant = crud.delete_claimant(db=db, claimant_id=claimant_id)
    if deleted_claimant is None:
        raise HTTPException(status_code=404, detail="Claimant not found")
    return deleted_claimant

# US6: Get services within a claimant's travel area
@app.get("/services/within/claimant/{claimant_id}", response_model=list[schemas.Service])
def get_services_for_claimant_area(claimant_id: int, db: Session = Depends(get_db)):
    claimant = crud.get_claimant(db, claimant_id=claimant_id)
    if not claimant:
        raise HTTPException(status_code=404, detail="Claimant not found")

    if not claimant.travel_extent_geojson:
        # Or return empty list with a specific message/status if preferred
        raise HTTPException(status_code=400, detail="Claimant does not have a defined travel extent")

    # The travel_extent_geojson is already a dict (from JSONB or from Shapely's mapping)
    services_within_extent = crud.get_services_within_geojson(db, geometry_filter=claimant.travel_extent_geojson)
    return services_within_extent
