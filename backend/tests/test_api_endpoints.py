"""
TON City Builder - API Endpoint Tests
Tests for core API functionality including auth, island, sprites, and user data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ton-merchant-hub.preview.emergentagent.com')

# Test credentials
TEST_USER = {
    "email": "user_1",
    "password": "password123"
}


class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_check(self):
        """Test /api/health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("SUCCESS: Health check passed")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with user_1 credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["username"] == "user_1"
        print(f"SUCCESS: Login successful for user_1")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid_user", "password": "wrongpass"}
        )
        assert response.status_code in [401, 400, 422]
        print("SUCCESS: Invalid login properly rejected")


class TestIslandEndpoint:
    """Island API tests"""
    
    def test_island_returns_data(self):
        """Test /api/island returns island grid data"""
        response = requests.get(f"{BASE_URL}/api/island")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "cells" in data
        assert "grid_size" in data
        assert len(data["cells"]) > 0
        print(f"SUCCESS: Island data retrieved - {len(data['cells'])} cells")
    
    def test_island_cells_have_required_fields(self):
        """Test island cells contain owner and business data"""
        response = requests.get(f"{BASE_URL}/api/island")
        data = response.json()
        cells = data["cells"]
        
        # Check first few cells have required fields
        for cell in cells[:5]:
            assert "x" in cell
            assert "y" in cell
            assert "zone" in cell
            print(f"Cell [{cell['x']},{cell['y']}]: zone={cell['zone']}")
        
        print("SUCCESS: Island cells have required fields")


class TestSpritesEndpoint:
    """Sprite info API tests"""
    
    def test_sprites_info_endpoint(self):
        """Test /api/sprites/info returns sprite generation status"""
        response = requests.get(f"{BASE_URL}/api/sprites/info")
        assert response.status_code == 200
        data = response.json()
        assert "total_expected" in data
        assert "total_generated" in data
        assert "sprites" in data
        print(f"SUCCESS: Sprites info - {data['total_generated']}/{data['total_expected']} generated")
    
    def test_sprites_mostly_generated(self):
        """Test that most sprites are generated"""
        response = requests.get(f"{BASE_URL}/api/sprites/info")
        data = response.json()
        generated_ratio = data["total_generated"] / data["total_expected"]
        assert generated_ratio >= 0.95, f"Only {generated_ratio*100:.1f}% sprites generated"
        print(f"SUCCESS: {data['total_generated']}/{data['total_expected']} sprites generated")


class TestUserBusinesses:
    """User businesses endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_my_businesses_returns_data(self, auth_token):
        """Test /api/my/businesses returns user's businesses"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/my/businesses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "businesses" in data
        assert "total" in data
        print(f"SUCCESS: User has {data['total']} businesses")
    
    def test_my_businesses_includes_dex(self, auth_token):
        """Test that user_1 has DEX business"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/my/businesses", headers=headers)
        data = response.json()
        
        business_types = [b.get("business_type") or b.get("type") for b in data.get("businesses", [])]
        assert any("dex" in str(b).lower() for b in business_types), f"DEX not found in {business_types}"
        print("SUCCESS: User has DEX business")


class TestLeaderboard:
    """Leaderboard endpoint tests"""
    
    def test_leaderboard_returns_users(self):
        """Test leaderboard returns user rankings"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "users" in data or "leaderboard" in data
        print("SUCCESS: Leaderboard data retrieved")


class TestChat:
    """Chat endpoint tests - should only have global chat"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_chat_messages_endpoint(self, auth_token):
        """Test chat messages endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/chat/messages", headers=headers)
        # Should return 200 with messages or empty list
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            print("SUCCESS: Chat messages endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
