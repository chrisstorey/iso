# This is the schemas.py file for Pydantic schemas.
from pydantic import BaseModel
from typing import List, Optional

# Basic Service Schema (expand according to ORUK standard)
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    fees: Optional[str] = None # For cost filtering, could be more structured.
    category: Optional[str] = None # For category filtering.

class ServiceCreate(ServiceBase):
    # Explicitly add latitude and longitude for creation
    # These will be used by crud.create_service to create the geometry/JSON location field
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pass

class ServiceUpdate(BaseModel): # Not inheriting ServiceBase to make all fields truly optional for PATCH
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    fees: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Service(ServiceBase):
    id: int
    # location will be handled by the model's conditional type.
    # If it's JSON, it might appear here. If it's Geometry, Pydantic might not show it by default
    # unless there's a specific serializer. For now, let's assume it might be a dict if JSON.
    location: Optional[dict] = None # To hold GeoJSON-like structure if model uses JSON type

    class Config:
        from_attributes = True # Replaces orm_mode in Pydantic v2

# Claimant Schemas
class ClaimantBase(BaseModel):
    name: str
    home_latitude: float
    home_longitude: float

class ClaimantCreate(ClaimantBase):
    pass

class ClaimantUpdate(BaseModel):
    name: Optional[str] = None
    home_latitude: Optional[float] = None
    home_longitude: Optional[float] = None
    # travel_radius_miles: Optional[float] = None # If we want to update radius

class Claimant(ClaimantBase):
    id: int
    travel_extent_geojson: Optional[dict] = None # GeoJSON structure for the travel area

    class Config:
        from_attributes = True
