"""
Test configuration and fixtures for the AI Search Engine backend.
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

# Set up test environment variables before importing the app
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_testing_only")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/")
os.environ.setdefault("DB_NAME", "test_ai_search_db")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("GOOGLE_API_KEY", "test_google_api_key")
os.environ.setdefault("GOOGLE_CX", "test_google_cx")

# Mock database collections before importing the app
mock_users_col = MagicMock()
mock_profiles_col = MagicMock()
mock_queries_col = MagicMock()
mock_interactions_col = MagicMock()
mock_discarded_tokens_col = MagicMock()

# Configure mock return values
mock_users_col.find_one.return_value = None  # No existing user by default
mock_queries_col.distinct.return_value = []  # No user IDs by default

with patch("backend.services.db.users_col", mock_users_col), \
     patch("backend.services.db.user_profiles_col", mock_profiles_col), \
     patch("backend.services.db.queries_col", mock_queries_col), \
     patch("backend.services.db.interactions_col", mock_interactions_col), \
     patch("backend.services.db.discarded_tokens_col", mock_discarded_tokens_col), \
     patch("backend.background_tasks.background_tasks.start_background_tasks"), \
     patch("backend.background_tasks.background_tasks.stop_background_tasks"):
    from backend.main import app


@pytest.fixture
def test_app():
    """
    Provide access to the FastAPI app instance for dependency overrides.
    Cleans up any overrides after the test.
    """
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    This fixture provides a TestClient instance that can be used to make
    requests to the API endpoints without running a server.
    """
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def mock_db():
    """
    Mock database collections to avoid actual database operations during tests.
    Returns a dictionary of mocked MongoDB collections.
    """
    return {
        "users": mock_users_col,
        "profiles": mock_profiles_col,
        "queries": mock_queries_col,
        "interactions": mock_interactions_col,
        "discarded_tokens": mock_discarded_tokens_col
    }


@pytest.fixture
def mock_auth_service():
    """
    Mock authentication service for testing auth-protected endpoints.
    """
    with patch("backend.api.auth_routes.auth_service") as mock_service:
        # Setup default mock behaviors
        mock_service.create_user.return_value = {
            "user_id": "test_user_123",
            "username": "testuser",
            "email": "test@example.com"
        }
        mock_service.authenticate_user.return_value = {
            "user_id": "test_user_123",
            "username": "testuser"
        }
        mock_service.create_access_token.return_value = "mock_token_12345"
        yield mock_service


@pytest.fixture
def mock_search_service():
    """
    Mock search service to avoid making actual API calls during tests.
    """
    with patch("backend.api.search_routes.search") as mock_search:
        mock_search.return_value = {
            "results": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "This is a test result"
                }
            ],
            "query": "test query",
            "expanded_query": "test query expanded"
        }
        yield mock_search


@pytest.fixture
def mock_user_profile():
    """
    Mock user profile data for testing profile-related endpoints.
    """
    return {
        "user_id": "test_user_123",
        "explicit_interests": [
            {"keyword": "python", "weight": 1.0, "last_updated": "2026-01-24T00:00:00"}
        ],
        "implicit_interests": {
            "machine learning": 0.8,
            "web development": 0.6
        },
        "implicit_exclusions": ["sports", "fashion"]
    }


@pytest.fixture
def valid_auth_token():
    """
    Provide a valid mock authentication token for testing protected endpoints.
    """
    return "Bearer mock_token_12345"


@pytest.fixture
def mock_logging_service():
    """
    Mock logging service to avoid database writes during tests.
    """
    with patch("backend.api.search_routes.log_query") as mock_log_query, \
         patch("backend.api.search_routes.log_interaction") as mock_log_interaction, \
         patch("backend.api.search_routes.log_feedback") as mock_log_feedback:
        yield {
            "log_query": mock_log_query,
            "log_interaction": mock_log_interaction,
            "log_feedback": mock_log_feedback
        }
