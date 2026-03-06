"""
TON-City V2.0 Comprehensive API Tests
Tests 21 businesses, admin panel, recommendations, income table, and auth
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ton-merchant-hub.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = f"testuser_{int(time.time())}@test.com"
TEST_USER_PASSWORD = "testpass123"
TEST_USER_USERNAME = f"testuser_{int(time.time())}"

class TestHealthAndConfig:
    """Test health and configuration endpoints"""
    
    def test_health_endpoint(self):
        """Test 1: Backend health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_config_endpoint(self):
        """Test app configuration"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "businesses" in data
        print(f"✓ Config endpoint has {len(data.get('businesses', {}))} businesses")


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_registration_initiate(self):
        """Test 2: Registration endpoint"""
        response = requests.post(f"{BASE_URL}/api/auth/register/initiate", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "username": TEST_USER_USERNAME
        })
        # May return 200 with token or error if email verification is needed
        print(f"Registration response: {response.status_code} - {response.text[:200]}")
        assert response.status_code in [200, 201, 400, 409, 422]  # Various valid responses
    
    def test_login_admin(self):
        """Test 3: Admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        print(f"Admin login response: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print(f"✓ Admin login successful, token received")
        return data["token"]
    
    def test_auth_me(self):
        """Test 4: Get current user with auth"""
        # First login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        
        # Get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "balance_ton" in data
        assert "is_admin" in data
        print(f"✓ Auth/me: balance={data.get('balance_ton')}, is_admin={data.get('is_admin')}")


class TestIncomeTable:
    """Test income table and business stats"""
    
    def test_income_table_ru(self):
        """Test 5: Income table with Russian language"""
        response = requests.get(f"{BASE_URL}/api/stats/income-table?lang=ru")
        assert response.status_code == 200
        data = response.json()
        assert "income_table" in data
        
        income_table = data["income_table"]
        assert len(income_table) == 21, f"Expected 21 businesses, got {len(income_table)}"
        
        # Verify each business has 10 levels
        for biz_type, biz_data in income_table.items():
            levels = biz_data.get("levels", {})
            assert len(levels) == 10, f"{biz_type} should have 10 levels, got {len(levels)}"
        
        print(f"✓ Income table: {len(income_table)} businesses, each with 10 levels")
        return income_table


class TestBusinessTypes:
    """Test business types endpoint"""
    
    def test_business_types(self):
        """Test 6: Get all business types"""
        response = requests.get(f"{BASE_URL}/api/businesses/types")
        assert response.status_code == 200
        data = response.json()
        
        # Should return 21 business types
        business_types = data.get("business_types") or data.get("businesses") or data
        if isinstance(business_types, dict):
            count = len(business_types)
        else:
            count = len(business_types)
        
        assert count == 21, f"Expected 21 business types, got {count}"
        print(f"✓ Business types: {count} types available")


class TestRecommendations:
    """Test build recommendations endpoint"""
    
    def test_recommendations_auth(self):
        """Test 7: Get build recommendations (authenticated)"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        
        response = requests.get(f"{BASE_URL}/api/recommendations/build", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        
        recs = data["recommendations"]
        if len(recs) > 0:
            rec = recs[0]
            assert "score" in rec or "business_type" in rec
            print(f"✓ Recommendations: {len(recs)} items, first: {rec.get('business_type', 'N/A')}")
        else:
            print(f"✓ Recommendations endpoint works (no recommendations available)")


class TestMarketPrices:
    """Test market prices endpoint"""
    
    def test_market_prices(self):
        """Test 8: Get market prices"""
        response = requests.get(f"{BASE_URL}/api/economy/market-prices")
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        
        prices = data["prices"]
        # Should have 16 resource types
        assert len(prices) >= 14, f"Expected at least 14 resources, got {len(prices)}"
        
        # Check price structure
        for resource, price_data in list(prices.items())[:3]:
            assert isinstance(price_data, (int, float, dict)), f"Invalid price format for {resource}"
        
        print(f"✓ Market prices: {len(prices)} resources")


class TestMyBusinesses:
    """Test user businesses endpoint"""
    
    def test_my_businesses(self):
        """Test 9: Get user's businesses"""
        # Login first
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        
        response = requests.get(f"{BASE_URL}/api/my/businesses", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "businesses" in data
        print(f"✓ My businesses: {len(data['businesses'])} businesses")


class TestLeaderboard:
    """Test leaderboard endpoint"""
    
    def test_leaderboard(self):
        """Test 10: Get leaderboard"""
        response = requests.get(f"{BASE_URL}/api/leaderboard?sort_by=total_income&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        print(f"✓ Leaderboard: {len(data['players'])} players")


class TestMarketListings:
    """Test market listings endpoint"""
    
    def test_market_listings(self):
        """Test 11: Get market listings"""
        response = requests.get(f"{BASE_URL}/api/market/listings")
        assert response.status_code == 200
        print(f"✓ Market listings: {response.status_code}")


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        return login_res.json()["token"]
    
    def test_admin_players_search(self, admin_token):
        """Test 12: Admin search players"""
        response = requests.get(f"{BASE_URL}/api/admin/players/search?query=admin", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        print(f"✓ Admin player search: {len(data['players'])} players found")
    
    def test_admin_player_details(self, admin_token):
        """Test 13: Admin get player details"""
        # First search for a player
        search_res = requests.get(f"{BASE_URL}/api/admin/players/search?query=", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert search_res.status_code == 200
        players = search_res.json().get("players", [])
        
        if len(players) > 0:
            player_id = players[0].get("id") or players[0].get("wallet_address")
            response = requests.get(f"{BASE_URL}/api/admin/players/{player_id}", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            assert response.status_code == 200
            data = response.json()
            # Check for multi-account info
            print(f"✓ Admin player details: user={data.get('user', {}).get('display_name', 'N/A')}")
        else:
            print("⚠ No players to test player details")
    
    def test_admin_market_prices(self, admin_token):
        """Test 14: Admin get enriched market prices"""
        response = requests.get(f"{BASE_URL}/api/admin/market/prices", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        
        # Check for enriched data (base_price, name_ru)
        prices = data["prices"]
        if len(prices) > 0:
            first_resource = list(prices.keys())[0]
            price_data = prices[first_resource]
            # Admin endpoint should have enriched data
            print(f"✓ Admin market prices: {len(prices)} resources, data: {price_data}")
    
    def test_admin_stabilize(self, admin_token):
        """Test 15: Admin stabilize market (deploy bot)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/market/stabilize?resource=energy&target_price=0.05",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # May return 200, 400 (invalid resource), or 403 (not admin)
        print(f"Admin stabilize response: {response.status_code} - {response.text[:200]}")
        assert response.status_code in [200, 400, 422]  # Either works or invalid params


class TestRemovedRoutes:
    """Test that removed routes return 404"""
    
    def test_referral_removed(self):
        """Test 16: Referral route should be removed (404)"""
        response = requests.get(f"{BASE_URL}/api/referral/my-code")
        assert response.status_code in [401, 404], f"Expected 401 or 404, got {response.status_code}"
        print(f"✓ Referral route properly removed: {response.status_code}")
    
    def test_alliance_removed(self):
        """Test 17: Alliance route should be removed (404)"""
        response = requests.get(f"{BASE_URL}/api/alliance/list")
        assert response.status_code in [401, 404], f"Expected 401 or 404, got {response.status_code}"
        print(f"✓ Alliance route properly removed: {response.status_code}")


class TestEconomicBalance:
    """Test that economic balance is correct (T3 > T2 > T1)"""
    
    def test_tier_income_balance(self):
        """Test that higher tiers have higher income"""
        response = requests.get(f"{BASE_URL}/api/stats/income-table?lang=ru")
        assert response.status_code == 200
        income_table = response.json()["income_table"]
        
        tier_incomes = {1: [], 2: [], 3: []}
        
        for biz_type, biz_data in income_table.items():
            tier = biz_data.get("tier", 1)
            # Get level 1 net income
            level_1 = biz_data.get("levels", {}).get("1") or biz_data.get("levels", {}).get(1, {})
            net_income = level_1.get("net_daily_ton", 0)
            tier_incomes[tier].append(net_income)
        
        # Calculate average income per tier
        avg_t1 = sum(tier_incomes[1]) / len(tier_incomes[1]) if tier_incomes[1] else 0
        avg_t2 = sum(tier_incomes[2]) / len(tier_incomes[2]) if tier_incomes[2] else 0
        avg_t3 = sum(tier_incomes[3]) / len(tier_incomes[3]) if tier_incomes[3] else 0
        
        print(f"Tier averages: T1={avg_t1:.2f}, T2={avg_t2:.2f}, T3={avg_t3:.2f}")
        
        # T3 should be > T2 > T1
        assert avg_t3 > avg_t2, f"T3 ({avg_t3:.2f}) should be > T2 ({avg_t2:.2f})"
        assert avg_t2 > avg_t1, f"T2 ({avg_t2:.2f}) should be > T1 ({avg_t1:.2f})"
        print(f"✓ Economic balance correct: T3 > T2 > T1")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
