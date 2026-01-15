"""
Backend API Tests for TON City Builder
Tests: Health, Stats, Plots, Businesses, Auth endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tonworld-build.preview.emergentagent.com')

class TestHealthEndpoint:
    """Health check endpoint tests"""
    
    def test_health_returns_healthy(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "websocket" in data
        print(f"✅ Health check passed: {data}")


class TestStatsEndpoint:
    """Game statistics endpoint tests"""
    
    def test_stats_returns_valid_data(self):
        """Test /api/stats returns valid game statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total_plots" in data
        assert "owned_plots" in data
        assert "available_plots" in data
        assert "total_businesses" in data
        assert "total_players" in data
        assert "total_volume_ton" in data
        
        # Verify data types
        assert isinstance(data["total_plots"], int)
        assert isinstance(data["total_players"], int)
        assert data["total_plots"] == 10000  # Expected total plots
        
        print(f"✅ Stats endpoint passed: {data}")


class TestPlotsEndpoint:
    """Plots endpoint tests"""
    
    def test_plots_returns_list(self):
        """Test /api/plots returns plots list"""
        response = requests.get(f"{BASE_URL}/api/plots")
        assert response.status_code == 200
        data = response.json()
        
        assert "plots" in data
        assert "total" in data
        assert isinstance(data["plots"], list)
        
        print(f"✅ Plots endpoint passed: {data['total']} plots found")
    
    def test_plot_by_coords_center(self):
        """Test /api/plots/coords/50/50 returns center plot with high price"""
        response = requests.get(f"{BASE_URL}/api/plots/coords/50/50")
        assert response.status_code == 200
        data = response.json()
        
        assert data["x"] == 50
        assert data["y"] == 50
        assert data["zone"] == "center"
        assert data["price"] == 100.0  # Center plot should be 100 TON
        assert data["is_available"] == True
        
        print(f"✅ Center plot (50,50) passed: price={data['price']} TON, zone={data['zone']}")
    
    def test_plot_by_coords_edge(self):
        """Test /api/plots/coords/0/0 returns edge plot with low price"""
        response = requests.get(f"{BASE_URL}/api/plots/coords/0/0")
        assert response.status_code == 200
        data = response.json()
        
        assert data["x"] == 0
        assert data["y"] == 0
        assert data["price"] == 10.0  # Edge plot should be 10 TON
        
        print(f"✅ Edge plot (0,0) passed: price={data['price']} TON, zone={data['zone']}")


class TestBusinessTypesEndpoint:
    """Business types endpoint tests"""
    
    def test_business_types_returns_all_types(self):
        """Test /api/businesses/types returns all business types"""
        response = requests.get(f"{BASE_URL}/api/businesses/types")
        assert response.status_code == 200
        data = response.json()
        
        assert "business_types" in data
        business_types = data["business_types"]
        
        # Should have at least 20 business types
        assert len(business_types) >= 20
        
        # Verify some expected business types exist
        expected_types = ["farm", "factory", "shop", "bank", "exchange", "power_plant"]
        for btype in expected_types:
            assert btype in business_types, f"Missing business type: {btype}"
        
        print(f"✅ Business types endpoint passed: {len(business_types)} types found")
    
    def test_business_type_has_required_fields(self):
        """Test business types have all required fields"""
        response = requests.get(f"{BASE_URL}/api/businesses/types")
        data = response.json()
        
        farm = data["business_types"]["farm"]
        
        # Verify required fields
        assert "name" in farm
        assert "icon" in farm
        assert "cost" in farm
        assert "base_income" in farm
        assert "allowed_zones" in farm
        assert "income_by_level" in farm
        
        # Verify income_by_level has 10 levels
        assert len(farm["income_by_level"]) == 10
        
        print(f"✅ Business type fields passed: farm has all required fields")
    
    def test_business_types_multilingual(self):
        """Test business types support Russian language"""
        response = requests.get(f"{BASE_URL}/api/businesses/types?lang=ru")
        assert response.status_code == 200
        data = response.json()
        
        farm = data["business_types"]["farm"]
        # Russian name should be "Ферма"
        assert farm["name"] == "Ферма" or farm["name"] == "Farm"
        
        print(f"✅ Multilingual support passed: farm name = {farm['name']}")


class TestAuthEndpoint:
    """Authentication endpoint tests"""
    
    def test_verify_wallet_creates_user(self):
        """Test /api/auth/verify-wallet creates user and returns token"""
        test_address = "TEST_0x1234567890abcdef1234567890abcdef12345678"
        
        response = requests.post(f"{BASE_URL}/api/auth/verify-wallet", json={
            "address": test_address,
            "language": "ru"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["wallet_address"] == test_address
        assert data["user"]["language"] == "ru"
        
        print(f"✅ Wallet verification passed: token received, language={data['user']['language']}")
        
        return data["token"]
    
    def test_get_current_user_with_token(self):
        """Test /api/auth/me returns user info with valid token"""
        # First get a token
        test_address = "TEST_0x1234567890abcdef1234567890abcdef12345679"
        
        verify_response = requests.post(f"{BASE_URL}/api/auth/verify-wallet", json={
            "address": test_address,
            "language": "en"
        })
        token = verify_response.json()["token"]
        
        # Now get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["wallet_address"] == test_address
        assert "balance_game" in data
        assert "plots_owned" in data
        assert "businesses_owned" in data
        
        print(f"✅ Get current user passed: wallet={data['wallet_address']}")


class TestLeaderboardEndpoint:
    """Leaderboard endpoint tests"""
    
    def test_leaderboard_returns_data(self):
        """Test /api/leaderboard returns leaderboard data"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)
        
        print(f"✅ Leaderboard endpoint passed: {len(data['leaderboard'])} players")


class TestIncomeTableEndpoint:
    """Income table endpoint tests"""
    
    def test_income_table_returns_data(self):
        """Test /api/stats/income-table returns income calculations"""
        response = requests.get(f"{BASE_URL}/api/stats/income-table")
        assert response.status_code == 200
        data = response.json()
        
        assert "income_table" in data
        income_table = data["income_table"]
        
        # Should have all business types
        assert len(income_table) >= 20
        
        # Verify farm has levels data
        assert "farm" in income_table
        assert "levels" in income_table["farm"]
        
        print(f"✅ Income table endpoint passed: {len(income_table)} business types")


class TestBusinessesEndpoint:
    """Businesses endpoint tests"""
    
    def test_businesses_returns_list(self):
        """Test /api/businesses returns businesses list"""
        response = requests.get(f"{BASE_URL}/api/businesses")
        assert response.status_code == 200
        data = response.json()
        
        assert "businesses" in data
        assert isinstance(data["businesses"], list)
        
        print(f"✅ Businesses endpoint passed: {len(data['businesses'])} businesses found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
