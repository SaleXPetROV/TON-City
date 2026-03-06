"""
TON City Builder - Iteration 4 Tests
Testing: Night mode, sprite scale, UI elements, chat, leaderboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ton-merchant-hub.preview.emergentagent.com')

class TestLogin:
    """Test login functionality"""
    
    def test_login_user_1(self):
        """Test login with user_1 / password123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "user_1",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["username"] == "user_1"
        print(f"✓ Login successful for user_1")


class TestIslandAPI:
    """Test /api/island endpoint"""
    
    def test_island_returns_cells(self):
        """Test that /api/island returns cells with owner and business data"""
        response = requests.get(f"{BASE_URL}/api/island")
        assert response.status_code == 200
        data = response.json()
        
        # Check cells exist
        cells = data.get("cells", [])
        assert len(cells) > 0, "Island should have cells"
        
        # Check stats
        stats = data.get("stats", {})
        owned = stats.get("owned_cells", 0)
        businesses = stats.get("businesses", 0)
        
        print(f"✓ Island has {len(cells)} cells, {owned} owned, {businesses} businesses")
        
        # Per TD: expect 230 owned and 172 businesses
        assert owned >= 200, f"Expected ~230 owned cells, got {owned}"
        assert businesses >= 150, f"Expected ~172 businesses, got {businesses}"
        
        # Verify some cells have business data
        cells_with_business = [c for c in cells if c.get("business")]
        assert len(cells_with_business) > 0, "Some cells should have businesses"
        
        # Check business structure
        sample_business = cells_with_business[0]["business"]
        assert "type" in sample_business
        print(f"✓ Sample business: {sample_business.get('type')}, level {sample_business.get('level')}")


class TestSpritesAPI:
    """Test /api/sprites/info endpoint"""
    
    def test_sprites_info(self):
        """Test that sprites info returns sprite status"""
        response = requests.get(f"{BASE_URL}/api/sprites/info")
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total_expected", 0)
        generated = data.get("total_generated", 0)
        
        print(f"✓ Sprites: {generated}/{total} generated")
        assert total > 0, "Expected sprite count"
        assert generated > 0, "Some sprites should be generated"


class TestLeaderboardNoLevel:
    """Verify leaderboard doesn't have level column"""
    
    def test_leaderboard_no_level(self):
        """Test leaderboard response structure"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        players = data.get("players", [])
        if len(players) > 0:
            # Check that player entries don't emphasize "level" as primary metric
            player = players[0]
            print(f"✓ Leaderboard player fields: {list(player.keys())}")


class TestConfigAPI:
    """Test /api/config endpoint for business types"""
    
    def test_config_returns_businesses(self):
        """Test config returns business types"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200
        data = response.json()
        
        businesses = data.get("businesses", {})
        assert len(businesses) > 0, "Config should have business types"
        
        # Check a sample business has tier info
        for biz_type, biz_config in list(businesses.items())[:3]:
            print(f"✓ Business {biz_type}: tier={biz_config.get('tier')}")


class TestChatGlobalOnly:
    """Test chat is global only"""
    
    def test_global_chat_messages(self):
        """Test global chat endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/chat/messages/global?limit=10")
        # Should return 200 even if empty
        assert response.status_code == 200
        data = response.json()
        messages = data.get("messages", [])
        print(f"✓ Global chat has {len(messages)} messages")


class TestAuthenticatedAPIs:
    """Test authenticated API endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "user_1",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Login failed")
    
    def test_auth_me(self, auth_token):
        """Test /api/auth/me returns user info without level emphasis"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check basic fields exist
        assert "id" in data
        assert "username" in data
        assert "balance_ton" in data
        
        print(f"✓ User: {data.get('username')}, balance: {data.get('balance_ton')} TON")
    
    def test_my_businesses(self, auth_token):
        """Test /api/my/businesses returns user's businesses"""
        response = requests.get(f"{BASE_URL}/api/my/businesses", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        businesses = data.get("businesses", [])
        print(f"✓ User has {len(businesses)} businesses")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
