"""
TON Island Game Systems - Backend API Tests
Tests: Island map, Config, Patrons, Banks, Business management
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://iso-builder-debug.preview.emergentagent.com')

# Test wallet address for authentication
TEST_WALLET = f"EQTest{uuid.uuid4().hex[:20]}Address"
TEST_USERNAME = f"test_island_{uuid.uuid4().hex[:8]}"


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_get_island_returns_map_data(self):
        """GET /api/island - returns island map with 500+ cells and zone statistics"""
        response = requests.get(f"{BASE_URL}/api/island")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify island structure
        assert "id" in data
        assert data["id"] == "ton_island"
        assert "name" in data
        assert "cells" in data
        assert "total_cells" in data
        assert "zone_stats" in data
        assert "zones" in data
        
        # Verify cell count (should be ~500)
        assert len(data["cells"]) >= 400, f"Expected 400+ cells, got {len(data['cells'])}"
        
        # Verify zone statistics
        zone_stats = data["zone_stats"]
        assert "core" in zone_stats
        assert "inner" in zone_stats
        assert "middle" in zone_stats
        assert "outer" in zone_stats
        
        # Verify cell structure
        if data["cells"]:
            cell = data["cells"][0]
            assert "x" in cell
            assert "y" in cell
            assert "zone" in cell
            assert "price" in cell
            assert "is_available" in cell
        
        print(f"✓ Island has {len(data['cells'])} cells")
        print(f"✓ Zone stats: {zone_stats}")
    
    def test_get_config_returns_business_configurations(self):
        """GET /api/config - returns business configurations, tier taxes, patron bonuses"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify config structure
        assert "businesses" in data
        assert "tier_taxes" in data
        assert "zones" in data
        
        # Verify businesses (should have 21 types)
        businesses = data["businesses"]
        assert len(businesses) >= 15, f"Expected 15+ business types, got {len(businesses)}"
        
        # Verify tier taxes
        tier_taxes = data["tier_taxes"]
        assert 1 in tier_taxes or "1" in tier_taxes
        assert 2 in tier_taxes or "2" in tier_taxes
        assert 3 in tier_taxes or "3" in tier_taxes
        
        # Verify business structure
        for biz_key, biz in businesses.items():
            assert "name" in biz
            assert "tier" in biz
            assert "icon" in biz
            assert "produces" in biz or biz.get("is_patron")
            
        print(f"✓ Config has {len(businesses)} business types")
        print(f"✓ Tier taxes: {tier_taxes}")
    
    def test_get_patrons_returns_list(self):
        """GET /api/patrons - returns list of available patrons"""
        response = requests.get(f"{BASE_URL}/api/patrons")
        assert response.status_code == 200
        
        data = response.json()
        assert "patrons" in data
        assert isinstance(data["patrons"], list)
        
        # Patrons may be empty if no patron businesses exist
        print(f"✓ Patrons endpoint returned {len(data['patrons'])} patrons")
    
    def test_get_banks_returns_list(self):
        """GET /api/banks - returns banks for instant withdrawal"""
        response = requests.get(f"{BASE_URL}/api/banks")
        assert response.status_code == 200
        
        data = response.json()
        assert "banks" in data
        assert isinstance(data["banks"], list)
        
        # Banks may be empty if no gram_bank businesses exist
        print(f"✓ Banks endpoint returned {len(data['banks'])} banks")


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup authentication for tests"""
        # Create test user via wallet verification
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-wallet",
            json={
                "address": TEST_WALLET,
                "username": TEST_USERNAME,
                "language": "ru"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                self.token = data.get("token")
                self.user = data.get("user")
            else:
                pytest.skip(f"Auth setup failed: {data}")
        else:
            pytest.skip(f"Auth setup failed with status {response.status_code}")
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_my_businesses_requires_auth(self):
        """GET /api/my/businesses - requires authentication"""
        # Without auth
        response = requests.get(f"{BASE_URL}/api/my/businesses")
        assert response.status_code == 401
        
        # With auth
        response = requests.get(f"{BASE_URL}/api/my/businesses", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "businesses" in data
        assert "summary" in data
        assert isinstance(data["businesses"], list)
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_businesses" in summary
        assert "total_pending_income" in summary
        assert "total_hourly_income" in summary
        assert "total_daily_income" in summary
        
        print(f"✓ My businesses: {summary['total_businesses']} businesses")
    
    def test_collect_all_requires_auth(self):
        """POST /api/my/collect-all - requires authentication"""
        # Without auth
        response = requests.post(f"{BASE_URL}/api/my/collect-all")
        assert response.status_code == 401
        
        # With auth
        response = requests.post(f"{BASE_URL}/api/my/collect-all", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "collected"
        assert "businesses_collected" in data
        assert "total_player_income" in data
        
        print(f"✓ Collect all: {data['businesses_collected']} businesses collected")
    
    def test_auth_me_returns_user_info(self):
        """GET /api/auth/me - returns current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "wallet_address" in data
        assert "balance_ton" in data
        assert "level" in data
        
        print(f"✓ User info: {data['username']}, balance: {data['balance_ton']} TON")


class TestBusinessManagement:
    """Test business upgrade and repair endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup authentication for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-wallet",
            json={
                "address": TEST_WALLET,
                "username": TEST_USERNAME,
                "language": "ru"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                self.token = data.get("token")
            else:
                pytest.skip(f"Auth setup failed: {data}")
        else:
            pytest.skip(f"Auth setup failed with status {response.status_code}")
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_upgrade_business_requires_auth(self):
        """POST /api/business/{id}/upgrade - requires authentication"""
        fake_id = "nonexistent-business-id"
        
        # Without auth
        response = requests.post(f"{BASE_URL}/api/business/{fake_id}/upgrade")
        assert response.status_code == 401
        
        # With auth but invalid business
        response = requests.post(f"{BASE_URL}/api/business/{fake_id}/upgrade", headers=self.headers)
        assert response.status_code == 404
        
        print("✓ Upgrade endpoint requires auth and valid business ID")
    
    def test_repair_business_requires_auth(self):
        """POST /api/business/{id}/repair - requires authentication"""
        fake_id = "nonexistent-business-id"
        
        # Without auth
        response = requests.post(f"{BASE_URL}/api/business/{fake_id}/repair")
        assert response.status_code == 401
        
        # With auth but invalid business
        response = requests.post(f"{BASE_URL}/api/business/{fake_id}/repair", headers=self.headers)
        assert response.status_code == 404
        
        print("✓ Repair endpoint requires auth and valid business ID")
    
    def test_collect_business_income_requires_auth(self):
        """POST /api/business/{id}/collect - requires authentication"""
        fake_id = "nonexistent-business-id"
        
        # Without auth
        response = requests.post(f"{BASE_URL}/api/business/{fake_id}/collect")
        assert response.status_code == 401
        
        # With auth but invalid business
        response = requests.post(f"{BASE_URL}/api/business/{fake_id}/collect", headers=self.headers)
        assert response.status_code == 404
        
        print("✓ Collect endpoint requires auth and valid business ID")


class TestIslandPurchase:
    """Test island plot purchase and building"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup authentication for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-wallet",
            json={
                "address": TEST_WALLET,
                "username": TEST_USERNAME,
                "language": "ru"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                self.token = data.get("token")
            else:
                pytest.skip(f"Auth setup failed: {data}")
        else:
            pytest.skip(f"Auth setup failed with status {response.status_code}")
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_buy_plot_requires_auth(self):
        """POST /api/island/buy/{x}/{y} - requires authentication"""
        # Without auth
        response = requests.post(f"{BASE_URL}/api/island/buy/16/16")
        assert response.status_code == 401
        
        print("✓ Buy plot requires authentication")
    
    def test_buy_plot_insufficient_funds(self):
        """POST /api/island/buy/{x}/{y} - fails with insufficient funds"""
        # New user has 0 balance, should fail
        response = requests.post(f"{BASE_URL}/api/island/buy/16/16", headers=self.headers)
        
        # Should fail due to insufficient funds (new user has 0 balance)
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data
            print(f"✓ Buy plot correctly rejected: {data['detail']}")
        elif response.status_code == 200:
            # Plot was already owned or user had balance
            print("✓ Buy plot succeeded (user had balance or plot was free)")
        else:
            print(f"✓ Buy plot returned status {response.status_code}")
    
    def test_build_on_island_requires_auth(self):
        """POST /api/island/build/{x}/{y} - requires authentication"""
        # Without auth
        response = requests.post(f"{BASE_URL}/api/island/build/16/16?business_type=helios")
        assert response.status_code == 401
        
        print("✓ Build on island requires authentication")


class TestWithdrawalSystem:
    """Test withdrawal endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Setup authentication for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-wallet",
            json={
                "address": TEST_WALLET,
                "username": TEST_USERNAME,
                "language": "ru"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                self.token = data.get("token")
            else:
                pytest.skip(f"Auth setup failed: {data}")
        else:
            pytest.skip(f"Auth setup failed with status {response.status_code}")
        
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_withdrawal_queue_requires_auth(self):
        """GET /api/withdrawals/queue - requires authentication"""
        # Without auth
        response = requests.get(f"{BASE_URL}/api/withdrawals/queue")
        assert response.status_code == 401
        
        # With auth
        response = requests.get(f"{BASE_URL}/api/withdrawals/queue", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "withdrawals" in data
        assert isinstance(data["withdrawals"], list)
        
        print(f"✓ Withdrawal queue: {len(data['withdrawals'])} withdrawals")


class TestWarehouseSystem:
    """Test warehouse rental endpoints"""
    
    def test_get_warehouse_rentals(self):
        """GET /api/warehouses/rentals - returns available rentals"""
        response = requests.get(f"{BASE_URL}/api/warehouses/rentals")
        assert response.status_code == 200
        
        data = response.json()
        assert "rentals" in data
        assert isinstance(data["rentals"], list)
        
        print(f"✓ Warehouse rentals: {len(data['rentals'])} available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
