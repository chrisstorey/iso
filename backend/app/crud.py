# This is the crud.py file for CRUD operations.
from sqlalchemy.orm import Session
from typing import Optional # Import Optional
from . import models, schemas
from shapely.geometry import Point, mapping # For creating Point and converting to GeoJSON
# from shapely.ops import transform # If reprojecting, not used in simple buffer yet
# import pyproj # For more accurate reprojection if needed, not used in simple buffer


# Service CRUD operations
def get_service(db: Session, service_id: int):
    return db.query(models.Service).filter(models.Service.id == service_id).first()

def get_services(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    fees: Optional[str] = None, # Assuming 'fees' field represents cost information for now
    # Add location filtering parameters here, e.g.,
    # min_lat: Optional[float] = None, max_lat: Optional[float] = None,
    # min_lon: Optional[float] = None, max_lon: Optional[float] = None,
    # within_claimant_id: Optional[int] = None # For more complex spatial queries
):
    query = db.query(models.Service)

    if category:
        query = query.filter(models.Service.category.ilike(f"%{category}%")) # Case-insensitive partial match

    if fees: # This is a simple string match; real cost filtering might be numeric (e.g. <= amount)
        query = query.filter(models.Service.fees.ilike(f"%{fees}%"))

    # Placeholder for location-based filtering
    # if min_lat is not None and max_lat is not None and min_lon is not None and max_lon is not None:
    #     if models.USE_GEOMETRY: # Check if we are using real Geometry
    #         from sqlalchemy import func # For ST_MakeEnvelope, ST_Within etc.
    #         # Example: Bounding box filter (PostGIS specific)
    #         # envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    #         # query = query.filter(func.ST_Within(models.Service.location, envelope))
    #         pass # Implement actual spatial query here
    #     else:
    #         # If using JSON for location, filtering would be more complex and less efficient
    #         # e.g., parse JSON and compare coordinates. Best to avoid complex queries on JSON.
    #         print("Warning: Location filtering requested but using JSON fallback for location.")
    #         pass

    print(f"crud.get_services: Querying with session bound to engine: {db.get_bind()}")
    return query.offset(skip).limit(limit).all()

def create_service(db: Session, service: schemas.ServiceCreate):
    # For services with locations, you'll need to handle the conversion
    # from lat/lon or GeoJSON in the schema to the WKT format for GeoAlchemy2 for USE_GEOMETRY=True case
    # For JSON fallback, it would just store the JSON.

    # Example with new fields, still basic location handling:
    db_service_data = service.model_dump(exclude={"latitude", "longitude"}) # Exclude lat/lon as they are not direct model fields

    location_data = None
    if service.latitude is not None and service.longitude is not None:
        if models.USE_GEOMETRY:
            # For PostGIS, GeoAlchemy2 handles WKT string or WKBElement
            # Creating a WKT string for simplicity here.
            # Ensure srid is 4326 for consistency, though the column definition should enforce it.
            location_data = f'SRID=4326;POINT({service.longitude} {service.latitude})'
            print(f"crud.create_service: Using WKT for location: {location_data}")
        else:
            # For JSON fallback in tests
            location_data = {"type": "Point", "coordinates": [service.longitude, service.latitude]}
            print(f"crud.create_service: Using JSON for location: {location_data}")

    db_service_data['location'] = location_data

    db_service = models.Service(**db_service_data)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def update_service(db: Session, service_id: int, service_update: schemas.ServiceUpdate) -> Optional[models.Service]:
    db_service = get_service(db, service_id=service_id)
    if not db_service:
        return None

    update_data = service_update.model_dump(exclude_unset=True) # Pydantic v2, only get provided fields

    # Handle location update if lat/lon are provided
    if 'latitude' in update_data and 'longitude' in update_data:
        lat = update_data.pop('latitude')
        lon = update_data.pop('longitude')
        if lat is not None and lon is not None:
            if models.USE_GEOMETRY:
                db_service.location = f'SRID=4326;POINT({lon} {lat})'
                print(f"crud.update_service: Updating WKT for location: {db_service.location}")
            else:
                db_service.location = {"type": "Point", "coordinates": [lon, lat]}
                print(f"crud.update_service: Updating JSON for location: {db_service.location}")
        else: # If one is provided but not the other, or they are null, clear location? Or error?
              # For now, if lat/lon are in update_data but null/incomplete, we could choose to clear location or ignore.
              # Let's assume if lat/lon are present in payload, they must be valid together, or location is set to None if one is missing.
              # If only one is provided, this logic makes it None. If both are None, it also makes it None.
            db_service.location = None
            print(f"crud.update_service: Lat/lon provided for update were incomplete/null, clearing location.")

    elif 'latitude' in update_data or 'longitude' in update_data:
        # If only one of lat/lon is provided, it's an invalid partial update for location.
        # Decide behavior: ignore, error, or clear location. For now, let's ignore partial lat/lon.
        # Or, ensure ServiceUpdate schema handles this (e.g. with a validator).
        # Current Pydantic model doesn't enforce they must come together if one is present.
        # We'll remove them to prevent individual application if only one is set.
        update_data.pop('latitude', None)
        update_data.pop('longitude', None)
        print("crud.update_service: Incomplete lat/lon in update, ignoring location change.")


    for key, value in update_data.items():
        setattr(db_service, key, value)

    db.add(db_service) # Not strictly necessary if db_service is already managed, but good practice.
    db.commit()
    db.refresh(db_service)
    return db_service

def delete_service(db: Session, service_id: int) -> Optional[models.Service]:
    db_service = get_service(db, service_id=service_id)
    if not db_service:
        return None
    db.delete(db_service)
    db.commit()
    return db_service


# Claimant CRUD operations
def get_claimant(db: Session, claimant_id: int):
    print(f"crud.get_claimant: Querying for claimant {claimant_id} with session bound to engine: {db.get_bind()}")
    return db.query(models.Claimant).filter(models.Claimant.id == claimant_id).first()

def get_claimants(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Claimant).offset(skip).limit(limit).all()

# Define a helper function to create a circular buffer
# This function is now at the module level
def create_circular_buffer_geojson(latitude: float, longitude: float, radius_miles: float) -> dict:
    # Approximate conversion: 1 degree latitude ~ 69 miles. 1 mile ~ 0.0145 degrees.
    # This is a simplification. Real-world applications should use projections (e.g., UTM) for accurate buffering in meters/miles.
    radius_degrees = radius_miles * (1 / 69.0) # Approximate

    home_point = Point(longitude, latitude)
    # Create a buffer (circle) around the point. quad_segs determines segments in a quarter circle.
    # resolution=16 in older Shapely is roughly quad_segs=4 or 8 for similar complexity.
    # Let's use quad_segs=8 for a reasonable approximation of a circle (32 segments total).
    buffer_polygon = home_point.buffer(radius_degrees, quad_segs=8)

    # Convert Shapely geometry to GeoJSON-like dictionary
    return mapping(buffer_polygon)


def create_claimant(db: Session, claimant: schemas.ClaimantCreate):
    # Default travel radius in miles
    DEFAULT_TRAVEL_RADIUS_MILES = 5.0

    travel_extent = create_circular_buffer_geojson(
        claimant.home_latitude,
        claimant.home_longitude,
        DEFAULT_TRAVEL_RADIUS_MILES
    )

    db_claimant_data = claimant.model_dump()
    db_claimant_data['travel_extent_geojson'] = travel_extent

    db_claimant = models.Claimant(**db_claimant_data)
    # db_claimant = models.Claimant(
    #     name=claimant.name,
    #     home_latitude=claimant.home_latitude,
    #     home_longitude=claimant.home_longitude,
    #     travel_extent_geojson=travel_extent
    # )
    db.add(db_claimant)
    db.commit()
    db.refresh(db_claimant)
    return db_claimant

def update_claimant(db: Session, claimant_id: int, claimant_update: schemas.ClaimantUpdate) -> Optional[models.Claimant]:
    db_claimant = get_claimant(db, claimant_id=claimant_id)
    if not db_claimant:
        return None

    update_data = claimant_update.model_dump(exclude_unset=True)

    recalculate_extent = False
    if "home_latitude" in update_data and db_claimant.home_latitude != update_data["home_latitude"]:
        setattr(db_claimant, "home_latitude", update_data["home_latitude"])
        recalculate_extent = True
    if "home_longitude" in update_data and db_claimant.home_longitude != update_data["home_longitude"]:
        setattr(db_claimant, "home_longitude", update_data["home_longitude"])
        recalculate_extent = True

    if "name" in update_data:
        setattr(db_claimant, "name", update_data["name"])

    if recalculate_extent:
        # Default travel radius in miles (should ideally be configurable or part of update payload)
        DEFAULT_TRAVEL_RADIUS_MILES = 5.0
        new_extent = create_circular_buffer_geojson(
            db_claimant.home_latitude, # Use the potentially updated lat/lon
            db_claimant.home_longitude,
            DEFAULT_TRAVEL_RADIUS_MILES
        )
        db_claimant.travel_extent_geojson = new_extent
        print(f"crud.update_claimant: Recalculated travel_extent_geojson: {new_extent}")

    db.add(db_claimant)
    db.commit()
    db.refresh(db_claimant)
    return db_claimant

def delete_claimant(db: Session, claimant_id: int) -> Optional[models.Claimant]:
    db_claimant = get_claimant(db, claimant_id=claimant_id)
    if not db_claimant:
        return None
    db.delete(db_claimant)
    db.commit()
    return db_claimant


# For US6: Get services within a given GeoJSON geometry
def get_services_within_geojson(db: Session, geometry_filter: dict) -> list[models.Service]:
    """
    Retrieves services that are geographically within the provided GeoJSON geometry.
    This implementation assumes PostGIS with ST_GeomFromGeoJSON and ST_Within.
    """
    if not models.USE_GEOMETRY: # models.USE_GEOMETRY is True if not TESTING or if USE_GEOMETRY_FOR_TESTS is true
        print("Warning: get_services_within_geojson called in an environment where USE_GEOMETRY is False (e.g., testing with JSON fallback). Spatial query will be skipped and return no results.")
        # Fallback: return an empty list, as JSON querying for spatial containment is complex and inefficient.
        # For a real test of this function, a PostGIS database would be required.
        return []

    from sqlalchemy import func # For ST_GeomFromGeoJSON, ST_SetSRID, ST_Within
    import json # To convert dict to JSON string for ST_GeomFromGeoJSON

    try:
        # Convert the GeoJSON dict to a JSON string
        geojson_str = json.dumps(geometry_filter)

        # Create a geometry object from the GeoJSON string and ensure it's SRID 4326
        # This assumes the input GeoJSON is in WGS84 (EPSG:4326)
        filter_geom = func.ST_SetSRID(func.ST_GeomFromGeoJSON(geojson_str), 4326)

        # Query services whose location is within the filter_geom
        # Assumes Service.location is a PostGIS Geometry column with SRID 4326
        query = db.query(models.Service).filter(
            func.ST_Within(models.Service.location, filter_geom)
        )
        return query.all()
    except Exception as e:
        print(f"Error in get_services_within_geojson: {e}")
        # Depending on how robust you want this, you might raise the error
        # or return an empty list / specific error response.
        return []
