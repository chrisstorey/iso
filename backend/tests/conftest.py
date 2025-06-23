import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
import platform
import os

# Import Base from the app's database module to ensure all models are known
from app.database import Base, get_db
from app.main import app

# --- Single Test Database Setup ---
# Use a named in-memory database with shared cache for the entire test suite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///file:main_test_db?mode=memory&cache=shared"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} # Needed for SQLite
    # echo=True # Uncomment for debugging SQL
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# SpatiaLite loading for the single test engine (if needed, though we fallback to JSON)
@event.listens_for(test_engine, "connect")
def load_spatialite_for_global_test_engine(dbapi_conn, connection_record):
    # This is mostly for completeness; models.py uses JSON for location in tests.
    # If actual spatial functions were tested with SQLite, this would be critical.
    spatialite_ext_name = "mod_spatialite"
    if platform.system() == "Linux":
        possible_ext_paths = ["mod_spatialite.so", "libspatialite.so"]
    elif platform.system() == "Darwin":
        possible_ext_paths = ["mod_spatialite.dylib", "/usr/local/lib/mod_spatialite.dylib"]
    elif platform.system() == "Windows":
        possible_ext_paths = ["mod_spatialite.dll"]
    else:
        possible_ext_paths = [spatialite_ext_name]

    cursor = dbapi_conn.cursor()
    try:
        if not hasattr(dbapi_conn, 'enable_load_extension'):
            print("Conftest: Warning: TestEngine dbapi_conn does not support enable_load_extension.")
        else:
            dbapi_conn.enable_load_extension(True)

        loaded = False
        for ext_path in possible_ext_paths:
            try:
                cursor.execute(f"SELECT load_extension('{ext_path}')")
                print(f"Conftest: TestEngine: Successfully loaded SpatiaLite: {ext_path}")
                loaded = True; break
            except Exception as e_inner_load: # Use a different variable name here
                # Suppress "not authorized" if it's common and expected due to sandbox setup
                if "not authorized" not in str(e_inner_load).lower():
                    print(f"Conftest: TestEngine: Failed to load SpatiaLite from {ext_path}: {e_inner_load}")

        # Check 'loaded' status. If not loaded, and the last error (e_inner_load) was not an auth error, then print.
        # This requires e_inner_load to be defined even if loop didn't run or all were auth errors.
        # A simpler way is to just report if not loaded, and separately mention auth errors are common.
        if not loaded:
             # This print might be redundant if individual load failures are already printed.
             # Consider a more consolidated message if preferred.
             print("Conftest: TestEngine: SpatiaLite extension could not be loaded (possibly due to authorization or missing library).")
    except Exception as e: # This is for errors like enable_load_extension failing
        print(f"Conftest: TestEngine: General error during SpatiaLite setup (e.g., enable_load_extension): {e}")
    finally:
        cursor.close()

# --- Fixtures ---

@pytest.fixture(scope="session")
def test_app_client():
    """
    Creates a TestClient instance for the app with the database dependency overridden.
    This override is applied once per session.
    """
    def override_get_db_for_tests():
        db = TestSessionLocal()
        try:
            # print(f"conftest.override_get_db_for_tests: Yielding session from {TestSessionLocal} bound to {db.get_bind()}")
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db_for_tests
    with TestClient(app) as client:
        # print("Conftest: TestClient created with get_db override.")
        yield client
    # Clean up override after session (optional, as it's usually fine for tests)
    # app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def manage_tables(test_app_client): # Ensures override is set before table creation
    """
    Handles table creation before each test and dropping after.
    Autouse ensures it runs for every test.
    """
    # print(f"conftest.manage_tables: Creating tables on engine: {test_engine}")
    Base.metadata.create_all(bind=test_engine)
    # print(f"conftest.manage_tables: Metadata tables: {Base.metadata.tables.keys()}")
    # Verify table creation (optional debug)
    with test_engine.connect() as connection:
        res_services = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='services';")).scalar_one_or_none()
        res_claimants = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='claimants';")).scalar_one_or_none()
        print(f"conftest.manage_tables: 'services' table exists: {res_services is not None}, 'claimants' table exists: {res_claimants is not None}")

    yield # Test runs here

    # print(f"conftest.manage_tables: Dropping tables on engine: {test_engine}")
    Base.metadata.drop_all(bind=test_engine)
    # print("conftest.manage_tables: Tables dropped.")

@pytest.fixture(scope="function")
def db_session_for_direct_use(manage_tables): # Depends on tables being created
    """
    Provides a DB session for tests that need to directly interact with the database.
    """
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Environment variable for testing, if not already set by the run command
os.environ["TESTING"] = "true"
# Ensure models.py uses JSON for Geometry by default in tests, unless USE_GEOMETRY_FOR_TESTS is true
if os.getenv("USE_GEOMETRY_FOR_TESTS", "false").lower() != "true":
    os.environ["USE_GEOMETRY_FOR_TESTS"] = "false"

print("Conftest.py loaded and test setup configured.")
