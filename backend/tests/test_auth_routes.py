"""
Tests for authentication routes (/auth/register, /auth/login).
"""
import pytest
from unittest.mock import patch


class TestAuthRoutes:
    """Test cases for authentication endpoints."""
    
    def test_register_success(self, client, mock_auth_service):
        """Test successful user registration with valid credentials."""
        # Arrange
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        
        # Act
        response = client.post("/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert data["username"] == "testuser"
        mock_auth_service.create_user.assert_called_once()
    
    def test_register_missing_username(self, client, mock_auth_service):
        """Test registration fails when username is missing."""
        # Arrange
        payload = {
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        
        # Act
        response = client.post("/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "username and password required" in response.json()["detail"]
    
    def test_register_missing_password(self, client, mock_auth_service):
        """Test registration fails when password is missing."""
        # Arrange
        payload = {
            "username": "newuser",
            "email": "newuser@example.com"
        }
        
        # Act
        response = client.post("/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "username and password required" in response.json()["detail"]
    
    def test_register_duplicate_user(self, client, mock_auth_service):
        """Test registration fails when username already exists."""
        # Arrange
        mock_auth_service.create_user.side_effect = ValueError("Username already exists")
        payload = {
            "username": "existinguser",
            "email": "existing@example.com",
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]
    
    def test_login_success(self, client, mock_auth_service):
        """Test successful login with valid credentials."""
        # Arrange
        payload = {
            "username": "testuser",
            "password": "correctpassword"
        }
        
        # Act
        response = client.post("/auth/login", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user_id" in data
        mock_auth_service.authenticate_user.assert_called_once_with("testuser", "correctpassword")
    
    def test_login_invalid_credentials(self, client, mock_auth_service):
        """Test login fails with incorrect credentials."""
        # Arrange
        mock_auth_service.authenticate_user.return_value = None
        payload = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        # Act
        response = client.post("/auth/login", json=payload)
        
        # Assert
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_missing_username(self, client, mock_auth_service):
        """Test login fails when username is missing."""
        # Arrange
        payload = {
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/login", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "username and password required" in response.json()["detail"]
    
    def test_login_missing_password(self, client, mock_auth_service):
        """Test login fails when password is missing."""
        # Arrange
        payload = {
            "username": "testuser"
        }
        
        # Act
        response = client.post("/auth/login", json=payload)
        
        # Assert
        assert response.status_code == 400
        assert "username and password required" in response.json()["detail"]
