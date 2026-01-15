"""
Backend API Tests for TON City Builder - Iteration 5
Testing new features: Tutorial modal, Online users counter, Treasury health
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tonworld-build.preview.emergentagent.com')

class TestHealthAndStats:
    """Health check and stats endpoints"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["websocket"] == True
        print("✅ Health endpoint working")
    
    def test_game_stats(self):
        """Test /api/stats returns game statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_plots" in data
        assert "total_players" in data
        assert "total_businesses" in data
        assert data["total_plots"] == 10000
        print(f"✅ Game stats: {data['total_players']} players, {data['owned_plots']} plots owned")


class TestOnlineUsersAPI:
    """Test online users counter API"""
    
    def test_online_stats_endpoint(self):
        """Test /api/stats/online returns online count"""
        response = requests.get(f"{BASE_URL}/api/stats/online")
        assert response.status_code == 200
        data = response.json()
        assert "online_count" in data
        assert isinstance(data["online_count"], int)
        assert data["online_count"] >= 0
        print(f"✅ Online users count: {data['online_count']}")
    
    def test_heartbeat_requires_auth(self):
        """Test /api/stats/heartbeat requires authentication"""
        response = requests.post(f"{BASE_URL}/api/stats/heartbeat")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]
        print("✅ Heartbeat endpoint requires authentication")


class TestTreasuryHealthAPI:
    """Test treasury health API (admin only)"""
    
    def test_treasury_health_requires_admin(self):
        """Test /api/admin/treasury-health requires admin auth"""
        response = requests.get(f"{BASE_URL}/api/admin/treasury-health")
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]
        print("✅ Treasury health endpoint requires admin authentication")


class TestIncomeTableAPI:
    """Test income table API for tutorial data"""
    
    def test_income_table_endpoint(self):
        """Test /api/stats/income-table returns income data"""
        response = requests.get(f"{BASE_URL}/api/stats/income-table?lang=en")
        assert response.status_code == 200
        data = response.json()
        assert "income_table" in data
        
        # Check that farm business type exists
        assert "farm" in data["income_table"]
        farm = data["income_table"]["farm"]
        assert "name" in farm
        assert "icon" in farm
        assert "levels" in farm
        print(f"✅ Income table has {len(data['income_table'])} business types")
    
    def test_income_table_russian(self):
        """Test income table with Russian language"""
        response = requests.get(f"{BASE_URL}/api/stats/income-table?lang=ru")
        assert response.status_code == 200
        data = response.json()
        
        # Check Russian name for farm
        farm = data["income_table"]["farm"]
        assert farm["name"] == "Ферма"
        print("✅ Income table Russian translation working")


class TestBusinessTypesAPI:
    """Test business types API"""
    
    def test_business_types_endpoint(self):
        """Test /api/businesses/types returns all business types"""
        response = requests.get(f"{BASE_URL}/api/businesses/types?lang=en")
        assert response.status_code == 200
        data = response.json()
        assert "business_types" in data
        
        # Should have 22 business types
        assert len(data["business_types"]) >= 20
        
        # Check required fields
        for biz_type, biz_data in data["business_types"].items():
            assert "name" in biz_data
            assert "icon" in biz_data
            assert "cost" in biz_data
            assert "sector" in biz_data
        
        print(f"✅ Business types: {len(data['business_types'])} types available")


class TestPlotsAPI:
    """Test plots API"""
    
    def test_plots_endpoint(self):
        """Test /api/plots returns plots list"""
        response = requests.get(f"{BASE_URL}/api/plots")
        assert response.status_code == 200
        data = response.json()
        assert "plots" in data
        assert "total" in data
        print(f"✅ Plots endpoint: {data['total']} plots in database")
    
    def test_plot_coords_center(self):
        """Test center plot (50,50) has highest price"""
        response = requests.get(f"{BASE_URL}/api/plots/coords/50/50")
        assert response.status_code == 200
        data = response.json()
        assert data["x"] == 50
        assert data["y"] == 50
        assert data["zone"] == "center"
        assert data["price"] == 100.0  # Center plots are most expensive
        print(f"✅ Center plot (50,50): {data['price']} TON, zone: {data['zone']}")
    
    def test_plot_coords_edge(self):
        """Test edge plot (0,0) has lowest price"""
        response = requests.get(f"{BASE_URL}/api/plots/coords/0/0")
        assert response.status_code == 200
        data = response.json()
        assert data["x"] == 0
        assert data["y"] == 0
        assert data["zone"] == "outskirts"
        assert data["price"] == 10.0  # Edge plots are cheapest
        print(f"✅ Edge plot (0,0): {data['price']} TON, zone: {data['zone']}")


class TestAuthAPI:
    """Test authentication API"""
    
    def test_wallet_verify(self):
        """Test wallet verification creates user"""
        test_address = f"TEST_wallet_{os.urandom(4).hex()}"
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-wallet",
            json={"address": test_address, "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["wallet_address"] == test_address
        print(f"✅ Wallet verification working, token received")
        return data["token"]
    
    def test_auth_me_with_token(self):
        """Test /api/auth/me returns user info with valid token"""
        # First get a token
        test_address = f"TEST_wallet_{os.urandom(4).hex()}"
        verify_response = requests.post(
            f"{BASE_URL}/api/auth/verify-wallet",
            json={"address": test_address, "language": "ru"}
        )
        token = verify_response.json()["token"]
        
        # Then test /api/auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["wallet_address"] == test_address
        assert data["language"] == "ru"
        print(f"✅ Auth me endpoint working with token")


class TestLeaderboardAPI:
    """Test leaderboard API"""
    
    def test_leaderboard_endpoint(self):
        """Test /api/leaderboard returns top players"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        print(f"✅ Leaderboard: {len(data['leaderboard'])} players")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
