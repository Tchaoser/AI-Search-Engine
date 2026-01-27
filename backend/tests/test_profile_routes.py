"""
Tests for user profile routes (/profiles/*).
"""
import pytest
from unittest.mock import patch, Mock


class TestProfileRoutes:
    """Test cases for user profile endpoints."""
    
    def test_get_user_profile_by_id(self, client, mock_user_profile):
        """Test retrieving any user's profile by user_id."""
        # Arrange
        with patch("services.user_profile_service.build_user_profile", return_value=mock_user_profile):
            
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
        with patch("api.utils.get_user_id_from_auth", return_value="test_user_123"):
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
        with patch("services.user_profile_service.build_user_profile", return_value=mock_user_profile):
            
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
        with patch("services.user_profile_service.build_user_profile", return_value=mock_user_profile):
            
            # Act
            response = client.get("/profiles/test_user_123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["implicit_interests"], dict)
