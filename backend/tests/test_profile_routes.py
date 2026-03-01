"""
Tests for user profile routes (/profiles/*).
"""
import pytest
from unittest.mock import patch, Mock
from backend.api.utils import get_user_id_from_auth, require_user_id_from_auth


class TestProfileRoutes:
    """Test cases for user profile endpoints."""
    
    def test_get_user_profile_by_id(self, client, mock_user_profile):
        """Test retrieving any user's profile by user_id."""
        # Arrange
        with patch("backend.services.user_profile_service.build_user_profile", return_value=mock_user_profile):
            
            # Act
            response = client.get("/profiles/test_user_123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["user_id"] == "test_user_123"
    
    def test_add_explicit_interest_missing_keyword(self, client):
        """Test adding explicit interest without keyword fails."""
        # Arrange
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"):
            payload = {
                "weight": 1.0
            }
            
            # Act
            response = client.post("/profiles/explicit/add", json=payload)
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_profile_endpoint_returns_correct_structure(self, client, mock_user_profile):
        """Test that profile response has the expected structure."""
        # Arrange
        with patch("backend.services.user_profile_service.build_user_profile", return_value=mock_user_profile):
            
            # Act
            response = client.get("/profiles/test_user_123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "user_id" in data
        assert "explicit_interests" in data
        assert "implicit_interests" in data
        
        # Verify explicit_interests structure
        if data["explicit_interests"]:
            first_interest = data["explicit_interests"][0]
            assert "keyword" in first_interest
            assert "weight" in first_interest
            assert "last_updated" in first_interest
    
    def test_profile_implicit_interests_as_dict(self, client, mock_user_profile):
        """Test that implicit_interests is returned as a dictionary."""
        # Arrange
        with patch("backend.services.user_profile_service.build_user_profile", return_value=mock_user_profile):
            
            # Act
            response = client.get("/profiles/test_user_123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["implicit_interests"], dict)


class TestMultiUserProfileIsolation:
    """Test cases verifying data isolation between multiple users."""

    @pytest.fixture
    def user_a_profile(self):
        """Profile data for User A."""
        return {
            "user_id": "user_a_123",
            "explicit_interests": [
                {"keyword": "python", "weight": 1.0, "last_updated": "2026-01-24T00:00:00"},
                {"keyword": "django", "weight": 0.8, "last_updated": "2026-01-24T00:00:00"}
            ],
            "implicit_interests": {
                "machine learning": 0.9,
                "web development": 0.7
            },
            "implicit_exclusions": ["cooking", "gardening"],
            "query_history": ["python tutorial", "django rest framework"],
            "click_history": ["docs.python.org", "djangoproject.com"],
            "last_updated": "2026-01-24T00:00:00",
            "profile_revision": 5
        }

    @pytest.fixture
    def user_b_profile(self):
        """Profile data for User B."""
        return {
            "user_id": "user_b_456",
            "explicit_interests": [
                {"keyword": "javascript", "weight": 1.0, "last_updated": "2026-01-25T00:00:00"},
                {"keyword": "react", "weight": 0.9, "last_updated": "2026-01-25T00:00:00"}
            ],
            "implicit_interests": {
                "frontend development": 0.85,
                "typescript": 0.6
            },
            "implicit_exclusions": ["backend", "databases"],
            "query_history": ["react hooks", "javascript async await"],
            "click_history": ["reactjs.org", "developer.mozilla.org"],
            "last_updated": "2026-01-25T00:00:00",
            "profile_revision": 3
        }

    @pytest.fixture
    def user_c_profile(self):
        """Profile data for User C (guest user scenario)."""
        return {
            "user_id": "guest",
            "explicit_interests": [],
            "implicit_interests": {},
            "implicit_exclusions": [],
            "query_history": [],
            "click_history": [],
            "last_updated": "2026-01-26T00:00:00",
            "profile_revision": 1
        }

    def test_different_users_get_different_profiles(self, client, user_a_profile, user_b_profile):
        """Test that different users receive their own distinct profiles."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_a = client.get("/profiles/user_a_123")
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_a.status_code == 200
        assert response_b.status_code == 200
        
        data_a = response_a.json()
        data_b = response_b.json()
        
        # Verify user IDs are correct
        assert data_a["user_id"] == "user_a_123"
        assert data_b["user_id"] == "user_b_456"
        
        # Verify explicit interests are different
        assert data_a["explicit_interests"] != data_b["explicit_interests"]
        keywords_a = {i["keyword"] for i in data_a["explicit_interests"]}
        keywords_b = {i["keyword"] for i in data_b["explicit_interests"]}
        assert keywords_a == {"python", "django"}
        assert keywords_b == {"javascript", "react"}
        
        # Verify implicit interests are different
        assert data_a["implicit_interests"] != data_b["implicit_interests"]
        assert "machine learning" in data_a["implicit_interests"]
        assert "frontend development" in data_b["implicit_interests"]

    def test_user_a_queries_not_in_user_b_profile(self, client, user_a_profile, user_b_profile):
        """Test that User A's query history does not appear in User B's profile."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_b.status_code == 200
        data_b = response_b.json()
        
        # User A's queries should NOT be in User B's profile
        user_a_queries = {"python tutorial", "django rest framework"}
        user_b_query_history = set(data_b.get("query_history", []))
        
        # No overlap between User A's queries and User B's history
        assert user_a_queries.isdisjoint(user_b_query_history)
        
        # User B should have their own queries
        assert "react hooks" in user_b_query_history or "javascript async await" in user_b_query_history

    def test_user_a_clicks_not_in_user_b_profile(self, client, user_a_profile, user_b_profile):
        """Test that User A's click history does not appear in User B's profile."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_b.status_code == 200
        data_b = response_b.json()
        
        # User A's clicks should NOT be in User B's profile
        user_a_clicks = {"docs.python.org", "djangoproject.com"}
        user_b_click_history = set(data_b.get("click_history", []))
        
        # No overlap between User A's clicks and User B's history
        assert user_a_clicks.isdisjoint(user_b_click_history)

    def test_user_a_explicit_interests_not_in_user_b(self, client, user_a_profile, user_b_profile):
        """Test that User A's explicit interests do not leak to User B."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_a = client.get("/profiles/user_a_123")
            response_b = client.get("/profiles/user_b_456")

        # Assert
        data_a = response_a.json()
        data_b = response_b.json()
        
        keywords_a = {i["keyword"].lower() for i in data_a["explicit_interests"]}
        keywords_b = {i["keyword"].lower() for i in data_b["explicit_interests"]}
        
        # No overlap in explicit interests
        assert keywords_a.isdisjoint(keywords_b)
        assert "python" in keywords_a
        assert "python" not in keywords_b
        assert "javascript" in keywords_b
        assert "javascript" not in keywords_a

    def test_user_a_implicit_interests_not_in_user_b(self, client, user_a_profile, user_b_profile):
        """Test that User A's implicit interests do not leak to User B."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_a = client.get("/profiles/user_a_123")
            response_b = client.get("/profiles/user_b_456")

        # Assert
        data_a = response_a.json()
        data_b = response_b.json()
        
        implicit_keys_a = set(data_a["implicit_interests"].keys())
        implicit_keys_b = set(data_b["implicit_interests"].keys())
        
        # No overlap in implicit interests
        assert implicit_keys_a.isdisjoint(implicit_keys_b)

    def test_add_explicit_interest_isolated_to_user(self, client, test_app, user_a_profile, user_b_profile):
        """Test that adding explicit interest to User A does not affect User B."""
        # Arrange
        updated_user_a_profile = user_a_profile.copy()
        updated_user_a_profile["explicit_interests"] = user_a_profile["explicit_interests"] + [
            {"keyword": "fastapi", "weight": 1.0, "last_updated": "2026-02-14T00:00:00"}
        ]
        
        # Track calls to return original profile first, then updated profile
        call_count = {"user_a": 0}
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                call_count["user_a"] += 1
                # First call returns original profile (for adding), subsequent calls return updated
                if call_count["user_a"] == 1:
                    return user_a_profile
                return updated_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            
            # Act - Add interest to User A
            response_add = client.post("/profiles/explicit/add", json={
                "keyword": "fastapi",
                "weight": 1.0
            })
            
            # Get User B's profile
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_add.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        keywords_b = {i["keyword"].lower() for i in data_b["explicit_interests"]}
        
        # User B should NOT have the new interest added to User A
        assert "fastapi" not in keywords_b

    def test_remove_explicit_interest_isolated_to_user(self, client, test_app, user_a_profile, user_b_profile):
        """Test that removing explicit interest from User A does not affect User B."""
        # Arrange
        updated_user_a_profile = user_a_profile.copy()
        updated_user_a_profile["explicit_interests"] = [
            i for i in user_a_profile["explicit_interests"] if i["keyword"] != "python"
        ]
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return updated_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            
            # Act - Remove interest from User A
            response_remove = client.request("DELETE", "/profiles/explicit/remove", json={
                "keyword": "python"
            })
            
            # Get User B's profile (unchanged)
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_remove.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B's profile should be unchanged
        keywords_b = {i["keyword"].lower() for i in data_b["explicit_interests"]}
        assert "javascript" in keywords_b
        assert "react" in keywords_b

    def test_bulk_update_isolated_to_user(self, client, test_app, user_a_profile, user_b_profile):
        """Test that bulk updating User A's interests does not affect User B."""
        # Arrange
        updated_user_a_profile = user_a_profile.copy()
        updated_user_a_profile["explicit_interests"] = [
            {"keyword": "python", "weight": 2.0, "last_updated": "2026-02-14T00:00:00"},
            {"keyword": "django", "weight": 1.5, "last_updated": "2026-02-14T00:00:00"}
        ]
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return updated_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            
            # Act - Bulk update User A
            response_update = client.put("/profiles/explicit/bulk_update", json={
                "updates": [
                    {"keyword": "python", "weight": 2.0},
                    {"keyword": "django", "weight": 1.5}
                ]
            })
            
            # Get User B's profile
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_update.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B's weights should be unchanged
        for interest in data_b["explicit_interests"]:
            if interest["keyword"] == "javascript":
                assert interest["weight"] == 1.0
            elif interest["keyword"] == "react":
                assert interest["weight"] == 0.9

    def test_implicit_exclusions_isolated_per_user(self, client, user_a_profile, user_b_profile):
        """Test that implicit exclusions are isolated per user."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_a = client.get("/profiles/user_a_123")
            response_b = client.get("/profiles/user_b_456")

        # Assert
        data_a = response_a.json()
        data_b = response_b.json()
        
        exclusions_a = set(data_a.get("implicit_exclusions", []))
        exclusions_b = set(data_b.get("implicit_exclusions", []))
        
        # Each user has their own exclusions
        assert "cooking" in exclusions_a
        assert "cooking" not in exclusions_b
        assert "backend" in exclusions_b
        assert "backend" not in exclusions_a

    def test_guest_user_has_empty_profile(self, client, user_c_profile):
        """Test that guest user has an empty profile with no data leakage."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "guest":
                return user_c_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response = client.get("/profiles/guest")

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "guest"
        assert data["explicit_interests"] == []
        assert data["implicit_interests"] == {}
        assert data["query_history"] == []
        assert data["click_history"] == []

    def test_authenticated_vs_guest_isolation(self, client, user_a_profile, user_c_profile):
        """Test that authenticated user data does not leak to guest profile."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "guest":
                return user_c_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_auth = client.get("/profiles/user_a_123")
            response_guest = client.get("/profiles/guest")

        # Assert
        data_auth = response_auth.json()
        data_guest = response_guest.json()
        
        # Authenticated user has data
        assert len(data_auth["explicit_interests"]) > 0
        assert len(data_auth["implicit_interests"]) > 0
        
        # Guest has no data
        assert len(data_guest["explicit_interests"]) == 0
        assert len(data_guest["implicit_interests"]) == 0

    def test_profile_me_returns_authenticated_user_profile(self, client, test_app, user_a_profile):
        """Test that /profiles/me returns the authenticated user's profile."""
        # Arrange
        async def override_require_user_id():
            return "user_a_123"

        test_app.dependency_overrides[require_user_id_from_auth] = override_require_user_id

        with patch("backend.api.profile_routes.build_user_profile", return_value=user_a_profile):
            # Act
            response = client.get("/profiles/me")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user_a_123"

    def test_profile_me_different_users_get_own_profiles(self, client, test_app, user_a_profile, user_b_profile):
        """Test that /profiles/me returns the correct profile for each authenticated user."""
        # Arrange & Act - User A
        async def override_require_user_id_a():
            return "user_a_123"

        test_app.dependency_overrides[require_user_id_from_auth] = override_require_user_id_a
        
        with patch("backend.api.profile_routes.build_user_profile", return_value=user_a_profile):
            response_a = client.get("/profiles/me")

        # Arrange & Act - User B
        async def override_require_user_id_b():
            return "user_b_456"

        test_app.dependency_overrides[require_user_id_from_auth] = override_require_user_id_b
        
        with patch("backend.api.profile_routes.build_user_profile", return_value=user_b_profile):
            response_b = client.get("/profiles/me")

        # Assert
        assert response_a.status_code == 200
        assert response_b.status_code == 200
        
        data_a = response_a.json()
        data_b = response_b.json()
        
        assert data_a["user_id"] == "user_a_123"
        assert data_b["user_id"] == "user_b_456"
        assert data_a["user_id"] != data_b["user_id"]

    def test_clear_explicit_interests_isolated_to_user(self, client, test_app, user_a_profile, user_b_profile):
        """Test that clearing User A's explicit interests does not affect User B."""
        # Arrange
        cleared_user_a_profile = user_a_profile.copy()
        cleared_user_a_profile["explicit_interests"] = []
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return cleared_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            
            # Act - Clear User A's explicit interests
            response_clear = client.post("/profiles/explicit/clear", json={})
            
            # Get User B's profile
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_clear.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B should still have their interests
        assert len(data_b["explicit_interests"]) == 2
        keywords_b = {i["keyword"] for i in data_b["explicit_interests"]}
        assert "javascript" in keywords_b
        assert "react" in keywords_b

    def test_clear_implicit_interests_isolated_to_user(self, client, test_app, user_a_profile, user_b_profile):
        """Test that clearing User A's implicit interests does not affect User B."""
        # Arrange
        cleared_user_a_profile = user_a_profile.copy()
        cleared_user_a_profile["implicit_interests"] = {}
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return cleared_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            mock_col.find_one.return_value = user_a_profile
            
            # Act - Clear User A's implicit interests
            response_clear = client.post("/profiles/implicit/clear", json={})
            
            # Get User B's profile
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_clear.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B should still have their implicit interests
        assert len(data_b["implicit_interests"]) == 2
        assert "frontend development" in data_b["implicit_interests"]
        assert "typescript" in data_b["implicit_interests"]

    def test_upgrade_implicit_to_explicit_isolated(self, client, test_app, user_a_profile, user_b_profile):
        """Test that upgrading implicit to explicit for User A does not affect User B."""
        # Arrange
        upgraded_user_a_profile = user_a_profile.copy()
        upgraded_user_a_profile["explicit_interests"] = user_a_profile["explicit_interests"] + [
            {"keyword": "machine learning", "weight": 1.0, "last_updated": "2026-02-14T00:00:00"}
        ]
        upgraded_user_a_profile["implicit_interests"] = {
            k: v for k, v in user_a_profile["implicit_interests"].items()
            if k != "machine learning"
        }
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return upgraded_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            mock_col.find_one.return_value = user_a_profile
            
            # Act - Upgrade implicit interest for User A
            response_upgrade = client.put("/profiles/implicit/upgrade", json={
                "keyword": "machine learning"
            })
            
            # Get User B's profile
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_upgrade.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B's profile should be unchanged
        explicit_keywords_b = {i["keyword"] for i in data_b["explicit_interests"]}
        assert "machine learning" not in explicit_keywords_b
        assert "frontend development" in data_b["implicit_interests"]

    def test_three_users_complete_isolation(self, client, user_a_profile, user_b_profile, user_c_profile):
        """Test complete isolation between three different users."""
        # Arrange
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            elif user_id == "guest":
                return user_c_profile
            return None

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile):
            # Act
            response_a = client.get("/profiles/user_a_123")
            response_b = client.get("/profiles/user_b_456")
            response_c = client.get("/profiles/guest")

        # Assert
        assert response_a.status_code == 200
        assert response_b.status_code == 200
        assert response_c.status_code == 200
        
        data_a = response_a.json()
        data_b = response_b.json()
        data_c = response_c.json()
        
        # All three users have distinct user_ids
        user_ids = {data_a["user_id"], data_b["user_id"], data_c["user_id"]}
        assert len(user_ids) == 3
        
        # Combine all interests from all users
        all_explicit_a = {i["keyword"].lower() for i in data_a["explicit_interests"]}
        all_explicit_b = {i["keyword"].lower() for i in data_b["explicit_interests"]}
        all_explicit_c = {i["keyword"].lower() for i in data_c["explicit_interests"]}
        
        # No overlap between any two users
        assert all_explicit_a.isdisjoint(all_explicit_b)
        assert all_explicit_a.isdisjoint(all_explicit_c)
        assert all_explicit_b.isdisjoint(all_explicit_c)

    def test_remove_implicit_interest_isolated(self, client, test_app, user_a_profile, user_b_profile):
        """Test that removing implicit interest from User A adds to exclusions without affecting User B."""
        # Arrange
        updated_user_a_profile = user_a_profile.copy()
        updated_user_a_profile["implicit_exclusions"] = user_a_profile["implicit_exclusions"] + ["machine learning"]
        updated_user_a_profile["implicit_interests"] = {
            k: v for k, v in user_a_profile["implicit_interests"].items()
            if k != "machine learning"
        }
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return updated_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            mock_col.find_one.return_value = user_a_profile
            
            # Act
            response_remove = client.request("DELETE", "/profiles/implicit/remove", json={
                "keyword": "machine learning"
            })
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_remove.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B's exclusions should NOT include "machine learning"
        assert "machine learning" not in data_b.get("implicit_exclusions", [])
        # User B should still have their implicit interests
        assert "frontend development" in data_b["implicit_interests"]

    def test_remove_implicit_exclusion_isolated(self, client, test_app, user_a_profile, user_b_profile):
        """Test that removing implicit exclusion from User A does not affect User B's exclusions."""
        # Arrange
        updated_user_a_profile = user_a_profile.copy()
        updated_user_a_profile["implicit_exclusions"] = [
            e for e in user_a_profile["implicit_exclusions"] if e != "cooking"
        ]
        
        def mock_build_profile(user_id, **kwargs):
            if user_id == "user_a_123":
                return updated_user_a_profile
            elif user_id == "user_b_456":
                return user_b_profile
            return None

        # Override FastAPI dependency
        async def override_get_user_id():
            return "user_a_123"

        test_app.dependency_overrides[get_user_id_from_auth] = override_get_user_id

        with patch("backend.api.profile_routes.build_user_profile", side_effect=mock_build_profile), \
             patch("backend.api.profile_routes.user_profiles_col") as mock_col:
            mock_col.find_one.return_value = user_a_profile
            
            # Act
            response_remove = client.request("DELETE", "/profiles/implicit/exclusion/remove", json={
                "keyword": "cooking"
            })
            response_b = client.get("/profiles/user_b_456")

        # Assert
        assert response_remove.status_code == 200
        assert response_b.status_code == 200
        
        data_b = response_b.json()
        # User B's exclusions should be unchanged
        assert "backend" in data_b.get("implicit_exclusions", [])
        assert "databases" in data_b.get("implicit_exclusions", [])
