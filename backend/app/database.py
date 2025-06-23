# This is the database.py file for database configuration.
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

#SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # For SQLite
# Use TEST_DATABASE_URL if running in test mode, otherwise use DATABASE_URL
# This helps ensure that main.py's create_all uses the test DB during test collection
from sqlalchemy import event # Add event
import platform # To check OS for SpatiaLite extension path

TESTING = os.getenv("TESTING", "false").lower() == "true"
if TESTING:
    # Use a named in-memory SQLite for the app's engine during testing, with shared cache
    # This helps if any part of the app setup (not overridden by tests) touches the DB.
    SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///file:app_test_db?mode=memory&cache=shared")
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) # SQLite specific

    # Load SpatiaLite extension for SQLite in testing
    # The path to mod_spatialite can vary. Common paths are checked.
    # This might need adjustment based on the execution environment.
    @event.listens_for(engine, "connect")
    def load_spatialite(dbapi_conn, connection_record):
        # Try common paths for mod_spatialite
        # On Linux, it might be libspatialite.so or mod_spatialite.so
        # On macOS, it might be /usr/local/lib/mod_spatialite.dylib
        # On Windows, mod_spatialite.dll
        # This is a common source of issues if the path is not found.
        # For simplicity, we'll try a common name. The actual path might need to be
        # configured or discovered more robustly in a real application.

        # Determine the extension name based on OS
        # This is a simplified approach. A robust solution might involve
        # trying multiple paths or allowing configuration via an env var.
        spatialite_ext_name = "mod_spatialite"
        if platform.system() == "Linux":
            # Try common names on Linux
            possible_ext_paths = ["mod_spatialite.so", "libspatialite.so"]
        elif platform.system() == "Darwin": # macOS
            possible_ext_paths = ["mod_spatialite.dylib", "/usr/local/lib/mod_spatialite.dylib"]
        elif platform.system() == "Windows":
            possible_ext_paths = ["mod_spatialite.dll"]
        else:
            possible_ext_paths = [spatialite_ext_name]

        cursor = dbapi_conn.cursor()
        cursor = dbapi_conn.cursor()
        try:
            # Check if enable_load_extension is available
            if not hasattr(dbapi_conn, 'enable_load_extension'):
                print("Warning: dbapi_conn does not support enable_load_extension. SpatiaLite may not load.")
                # Try loading directly if enable_load_extension is not present or needed by this sqlite3 version
                # This path is less likely to succeed if enable_load_extension=False by default
            else:
                dbapi_conn.enable_load_extension(True)

            loaded = False
            for ext_path in possible_ext_paths:
                try:
                    cursor.execute(f"SELECT load_extension('{ext_path}')")
                    print(f"Successfully loaded SpatiaLite extension: {ext_path} (for app.database.engine)")
                    loaded = True
                    break # Stop trying if one path works
                except Exception as e_load:
                    print(f"Failed to load SpatiaLite extension from {ext_path}: {e_load} (for app.database.engine)")

            if not loaded:
                 print("SpatiaLite extension could not be loaded for app.database.engine. Spatial features may be limited or fail.")

            # Re-disable if it was enabled and if possible (though usually left enabled for session)
            # if hasattr(dbapi_conn, 'enable_load_extension'):
            #     dbapi_conn.enable_load_extension(False)

        except Exception as e:
            print(f"General error during SpatiaLite loading for app.database.engine: {e}")
        finally:
            cursor.close()
else:
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/servicedb")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
