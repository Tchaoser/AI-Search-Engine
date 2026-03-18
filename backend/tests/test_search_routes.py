"""
Tests for search routes (/search).
"""
import pytest
from unittest.mock import patch, Mock


class TestSearchRoutes:
    """Test cases for search endpoints."""
    
    def test_search_without_enhanced_mode(self, client, mock_search_service, mock_logging_service):
        """Test search without semantic enhancement."""
        # Arrange
        with patch("backend.api.utils.get_user_id_from_auth", return_value="guest"):
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
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"):
            # Act - Test high verbosity
            response = client.get("/search?q=test&verbosity=high")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_with_semantic_modes(self, client, mock_search_service, mock_logging_service):
        """Test search with different semantic modes."""
        # Arrange
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"):
            # Act - Test clarify_and_personalize mode
            response = client.get("/search?q=test&semantic_mode=clarify_and_personalize")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_search_empty_query(self, client, mock_search_service, mock_logging_service):
        """Test search with an empty query string."""
        # Arrange
        with patch("backend.api.utils.get_user_id_from_auth", return_value="guest"):
            # Act
            response = client.get("/search?q=")
        
        # Assert
        # Empty query might still be accepted by the API but returns empty results
        # or an appropriate error - adjust based on actual behavior
        assert response.status_code in [200, 400, 422]
    
    def test_search_authenticated_user(self, client, mock_search_service, mock_logging_service):
        """Test search endpoint with authenticated user."""
        # Arrange
        with patch("backend.api.utils.get_user_id_from_auth", return_value="authenticated_user_456"):
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
        with patch("backend.api.utils.get_user_id_from_auth", return_value="guest"):
            # Act
            response = client.get("/search?q=C%2B%2B+programming")  # C++ encoded
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_search_benchmark_mode_returns_results(self, client, mock_search_service, mock_logging_service):
        """Test search with benchmark_mode=true returns results and flag."""
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"):
            response = client.get("/search?q=test&benchmark_mode=true")

        assert response.status_code == 200
        data = response.json()
        assert data["benchmark_mode"] is True
        assert "results" in data

    def test_search_benchmark_mode_skips_personalization(self, client, mock_logging_service):
        """Test that benchmark mode skips reranking and profile insight."""
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"), \
             patch("backend.api.search_routes.search") as mock_search, \
             patch("backend.api.search_routes.get_profile_insight") as mock_insight:
            mock_search.return_value = [{"title": "Raw Result", "link": "https://example.com"}]
            response = client.get("/search?q=test&benchmark_mode=true&use_enhanced=false")

        assert response.status_code == 200
        data = response.json()
        # search should be called with benchmark_mode=True
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args
        assert call_kwargs[1]["benchmark_mode"] is True
        # profile insight should NOT be fetched
        mock_insight.assert_not_called()
        assert data["profile_insight"] is None

    def test_search_normal_mode_uses_personalization(self, client, mock_logging_service):
        """Test that normal mode (no benchmark flag) still uses personalization."""
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"), \
             patch("backend.api.search_routes.search") as mock_search, \
             patch("backend.api.search_routes.get_profile_insight") as mock_insight:
            mock_search.return_value = [{"title": "Result", "link": "https://example.com"}]
            mock_insight.return_value = {"interests": ["python"]}
            response = client.get("/search?q=test&use_enhanced=false")

        assert response.status_code == 200
        data = response.json()
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args
        assert call_kwargs[1]["benchmark_mode"] is False
        mock_insight.assert_called_once()
        assert data.get("benchmark_mode") is False

    def test_search_benchmark_mode_controls_expansion(self, client, mock_search_service, mock_logging_service):
        """Test benchmark mode with explicit expansion parameters."""
        with patch("backend.api.utils.get_user_id_from_auth", return_value="test_user_123"):
            # Baseline: no expansion
            response = client.get("/search?q=test&benchmark_mode=true&use_enhanced=false")
            assert response.status_code == 200
            data = response.json()
            assert data["use_enhanced"] is False
            assert data["benchmark_mode"] is True

            # Expanded: with clarify_only
            response = client.get("/search?q=test&benchmark_mode=true&use_enhanced=true&semantic_mode=clarify_only")
            assert response.status_code == 200
            data = response.json()
            assert data["use_enhanced"] is True
            assert data["semantic_mode"] == "clarify_only"
            assert data["benchmark_mode"] is True
