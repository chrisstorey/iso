# This is the models.py file for SQLAlchemy models.
import os
from sqlalchemy import Column, Integer, String, Text, Float, JSON # Added JSON
# Use the Base from database.py to ensure models are registered with the same metadata
from .database import Base
# Conditionally import Geometry and set location type
USE_GEOMETRY = os.getenv("USE_GEOMETRY_FOR_TESTS", "false").lower() == "true" or not (os.getenv("TESTING", "false").lower() == "true")

if USE_GEOMETRY:
    from geoalchemy2 import Geometry
    LocationType = Geometry(geometry_type='POINT', srid=4326)
else:
    # Fallback for testing environments where SpatiaLite might not be available
    # Using JSON to store GeoJSON-like point data, or Text
    print(f"Models.py: TESTING={os.getenv('TESTING')}, USE_GEOMETRY_FOR_TESTS={os.getenv('USE_GEOMETRY_FOR_TESTS')}, Resolved USE_GEOMETRY={USE_GEOMETRY}")
    print("Models.py: Using JSON for location column in Service model.")
    LocationType = JSON


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    fees = Column(String, nullable=True) # Could be Text if long, or structured if cost is numeric
    category = Column(String, index=True, nullable=True) # index=True for faster filtering

    location = Column(LocationType, nullable=True)

    # If you want to store simple lat/lon separately as well (optional, can be derived from location)
    # latitude = Column(Float, nullable=True)
    # longitude = Column(Float, nullable=True)

class Claimant(Base):
    __tablename__ = "claimants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    home_latitude = Column(Float)
    home_longitude = Column(Float)

    # travel_extent_geojson will store a polygon representing the travel area.
    # It will be a Geometry type (e.g., Polygon) for PostGIS.
    # For SQLite testing, it will use the same LocationType fallback (JSON).
    travel_extent_geojson = Column(LocationType, nullable=True)
    # Note: LocationType is defined as Geometry or JSON based on USE_GEOMETRY
