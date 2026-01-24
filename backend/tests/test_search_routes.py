"""
Tests for search routes (/search).
"""
import pytest
from unittest.mock import patch, Mock


class TestSearchRoutes:
    """Test cases for search endpoints."""
    
    def test_search_basic_query(self, client, mock_search_service, mock_logging_service):
        """Test basic search with a simple query."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="guest"):
            # Act
            response = client.get("/search?q=python+programming")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        mock_search_service.assert_called_once()
    
    def test_search_with_enhanced_mode(self, client, mock_search_service, mock_logging_service):
        """Test search with semantic enhancement enabled."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="test_user_123"), \
             patch("services.semantic_expansion.expand_query") as mock_expand:
            mock_expand.return_value = {
                "expanded_query": "python programming language tutorial",
                "clarifications": []
            }
            
            # Act
            response = client.get("/search?q=python&use_enhanced=true")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data
    
    def test_search_without_enhanced_mode(self, client, mock_search_service, mock_logging_service):
        """Test search without semantic enhancement."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="guest"):
            # Act
            response = client.get("/search?q=test+query&use_enhanced=false")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_missing_query_parameter(self, client):
        """Test search fails when query parameter is missing."""
        # Act
        response = client.get("/search")
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity - missing required param
    
    def test_search_with_verbosity_settings(self, client, mock_search_service, mock_logging_service):
        """Test search with different verbosity levels."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="test_user_123"):
            # Act - Test high verbosity
            response = client.get("/search?q=test&verbosity=high")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_with_semantic_modes(self, client, mock_search_service, mock_logging_service):
        """Test search with different semantic modes."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="test_user_123"):
            # Act - Test clarify_and_personalize mode
            response = client.get("/search?q=test&semantic_mode=clarify_and_personalize")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_empty_query(self, client, mock_search_service, mock_logging_service):
        """Test search with an empty query string."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="guest"):
            # Act
            response = client.get("/search?q=")
        
        # Assert
        # Empty query might still be accepted by the API but returns empty results
        # or an appropriate error - adjust based on actual behavior
        assert response.status_code in [200, 400, 422]
    
    def test_search_authenticated_user(self, client, mock_search_service, mock_logging_service):
        """Test search endpoint with authenticated user."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="authenticated_user_456"):
            # Act
            response = client.get("/search?q=machine+learning")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Verify logging was called for authenticated user
        mock_logging_service["log_query"].assert_called_once()
    
    def test_search_special_characters(self, client, mock_search_service, mock_logging_service):
        """Test search with special characters in query."""
        # Arrange
        with patch("api.utils.get_user_id_from_auth", return_value="guest"):
            # Act
            response = client.get("/search?q=C%2B%2B+programming")  # C++ encoded
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
