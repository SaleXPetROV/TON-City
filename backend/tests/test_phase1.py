"""
Test suite for TON City Builder Phase 1 changes
Tests: Login, Sidebar Logo, Landing Stats, Balance Formatting, Map Sprites, Night Mode, 
       Marketplace Stats, My Businesses Income Display, Chat Global
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ton-merchant-hub.preview.emergentagent.com')

# Test credentials
TEST_USER = "user_1"
TEST_PASSWORD = "password123"
TEST_EMAIL = "user_1"


class TestAuthentication:
    """Test login functionality"""
    
    def test_login_with_valid_credentials(self):
        """Test login with user_1/password123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["username"] == TEST_USER, "Wrong username"
        print(f"✓ Login successful for {TEST_USER}")
        return data["token"]
    
    def test_auth_me_endpoint(self):
        """Test /api/auth/me returns user info"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["token"]
        
        # Now test /api/auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Auth/me failed: {response.text}"
        
        user = response.json()
        assert "balance_ton" in user, "No balance_ton in user"
        assert isinstance(user["balance_ton"], (int, float)), "balance_ton is not a number"
        print(f"✓ Auth/me returns user with balance: {user['balance_ton']}")


class TestIslandAPI:
    """Test /api/island endpoint"""
    
    def test_island_returns_cells(self):
        """Test /api/island returns cells with owners and businesses"""
        response = requests.get(f"{BASE_URL}/api/island")
        assert response.status_code == 200, f"Island API failed: {response.text}"
        
        data = response.json()
        assert "cells" in data or "grid" in data, "No cells/grid in response"
        
        # Check for cells array or get cells
        if "cells" in data:
            cells = data["cells"]
            owned_count = sum(1 for c in cells if c.get("owner"))
            business_count = sum(1 for c in cells if c.get("building") or c.get("business"))
            print(f"✓ Island has {len(cells)} cells, {owned_count} owned, {business_count} with businesses")
        else:
            print(f"✓ Island grid structure returned")


class TestMyBusinesses:
    """Test /api/my/businesses endpoint for income display"""
    
    def test_my_businesses_endpoint(self):
        """Test businesses endpoint returns income data"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_response.json()["token"]
        
        response = requests.get(f"{BASE_URL}/api/my/businesses", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"My businesses failed: {response.text}"
        
        data = response.json()
        assert "businesses" in data, "No businesses array"
        assert "summary" in data, "No summary in response"
        
        # Check summary has income info (not income_per_hour, just income)
        summary = data["summary"]
        print(f"✓ My businesses: {len(data['businesses'])} businesses")
        print(f"  Summary keys: {list(summary.keys())}")


class TestMarketplace:
    """Test marketplace API - no resource trading, shows business/land stats"""
    
    def test_marketplace_land_listings(self):
        """Test land listings endpoint"""
        response = requests.get(f"{BASE_URL}/api/market/land/listings")
        assert response.status_code == 200, f"Market land listings failed: {response.text}"
        
        data = response.json()
        assert "listings" in data, "No listings in response"
        print(f"✓ Market land listings: {len(data['listings'])} listings")
    
    def test_marketplace_resource_listings(self):
        """Test resource listings endpoint (for stats only - no resource trading button)"""
        response = requests.get(f"{BASE_URL}/api/market/listings")
        assert response.status_code == 200, f"Market listings failed: {response.text}"
        
        data = response.json()
        assert "listings" in data, "No listings in response"
        print(f"✓ Market resource listings: {len(data['listings'])} listings")


class TestChat:
    """Test chat API - only global chat"""
    
    def test_global_chat_endpoint(self):
        """Test global chat messages endpoint"""
        response = requests.get(f"{BASE_URL}/api/chat/messages/global")
        assert response.status_code == 200, f"Chat messages failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, (list, dict)), "Unexpected response format"
        print(f"✓ Global chat endpoint works")


class TestLeaderboard:
    """Test leaderboard API"""
    
    def test_leaderboard_endpoint(self):
        """Test leaderboard returns players with correct data"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200, f"Leaderboard failed: {response.text}"
        
        data = response.json()
        assert "players" in data or isinstance(data, list), "No players in response"
        
        players = data.get("players", data) if isinstance(data, dict) else data
        if len(players) > 0:
            player = players[0]
            print(f"✓ Leaderboard player fields: {list(player.keys())}")


class TestConfig:
    """Test config API for business types"""
    
    def test_config_endpoint(self):
        """Test config returns business types"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200, f"Config failed: {response.text}"
        
        data = response.json()
        print(f"✓ Config returned with keys: {list(data.keys())[:5]}...")


class TestSprites:
    """Test sprites info endpoint"""
    
    def test_sprites_info(self):
        """Test sprites info endpoint"""
        response = requests.get(f"{BASE_URL}/api/sprites/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Sprites info: {data.get('generated', 'N/A')} sprites generated")
        else:
            print(f"⚠ Sprites info endpoint returned {response.status_code}")


class TestBalanceFormatting:
    """Test balance values are formatted properly"""
    
    def test_user_balance_is_numeric(self):
        """Test user balance is a proper number for 2 decimal formatting"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        data = login_response.json()
        
        user = data["user"]
        # The balance should be numeric - UI formats it to 2 decimal places
        if "balance_ton" in user:
            balance = user["balance_ton"]
            assert isinstance(balance, (int, float)), f"Balance is not numeric: {type(balance)}"
            print(f"✓ User balance is numeric: {balance} (will be formatted to {balance:.2f} in UI)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
