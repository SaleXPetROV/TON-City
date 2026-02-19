#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for TON City Builder
Tests all backend functionality for the Russian TON City project
"""
import requests
import sys
import time
import json
from datetime import datetime

class TonCityBackendTester:
    def __init__(self, base_url="https://a6fe025d-8065-48a3-b1c3-46f7c53f601e.stage-preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = []

    def log_test(self, name, success, details=None, error_msg=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error_msg}")
            self.failed_tests.append({"name": name, "error": error_msg, "details": details})
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })

    def test_api_endpoint(self, name, method, endpoint, expected_status=200, data=None, headers=None, auth_required=False):
        """Generic API endpoint tester"""
        try:
            url = f"{self.api_url}/{endpoint}"
            request_headers = headers or {}
            
            if auth_required and self.token:
                request_headers['Authorization'] = f'Bearer {self.token}'
            elif auth_required and not self.token:
                self.log_test(name, False, error_msg="No auth token available")
                return False, {}
            
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=10)
            elif method == 'POST':
                request_headers['Content-Type'] = 'application/json'
                response = requests.post(url, json=data, headers=request_headers, timeout=10)
            elif method == 'PUT':
                request_headers['Content-Type'] = 'application/json' 
                response = requests.put(url, json=data, headers=request_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=10)
            else:
                self.log_test(name, False, error_msg=f"Unsupported method: {method}")
                return False, {}
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                if response.content:
                    response_data = response.json()
            except:
                response_data = {"raw_content": response.text[:200]}
            
            details = {
                "status_code": response.status_code,
                "expected": expected_status,
                "response_size": len(response.content),
                "url": url,
                "method": method
            }
            
            error_msg = None if success else f"Expected {expected_status}, got {response.status_code}"
            
            self.log_test(name, success, details, error_msg)
            return success, response_data
            
        except requests.exceptions.RequestException as e:
            self.log_test(name, False, error_msg=f"Request failed: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, error_msg=f"Test error: {str(e)}")
            return False, {}

    def test_maintenance_apis(self):
        """Test maintenance-related APIs"""
        print("\n🔧 Testing Maintenance APIs...")
        
        # Test public maintenance status endpoint
        success, data = self.test_api_endpoint(
            "GET /api/maintenance-status",
            "GET",
            "maintenance-status"
        )
        
        if success:
            print(f"   Maintenance status: {data.get('enabled', 'unknown')}")
        
        # Test admin maintenance endpoint (requires auth)
        if self.token:
            success, data = self.test_api_endpoint(
                "POST /api/admin/maintenance (toggle)",
                "POST", 
                "admin/maintenance",
                data={"enabled": False},  # Try to disable maintenance
                auth_required=True
            )

    def test_auth_system(self):
        """Test authentication system"""
        print("\n🔐 Testing Authentication System...")
        
        # Test wallet verification with test data
        test_wallet = "0:1234567890123456789012345678901234567890123456789012345678901234"
        test_username = f"test_user_{int(time.time())}"
        
        success, response = self.test_api_endpoint(
            "POST /api/auth/verify-wallet",
            "POST",
            "auth/verify-wallet",
            data={
                "address": test_wallet,
                "username": test_username,
                "language": "ru"
            }
        )
        
        if success and response.get("token"):
            self.token = response["token"]
            self.user_data = response.get("user", {})
            print(f"   ✅ Authenticated as: {self.user_data.get('username')}")
        
        # Test /auth/me endpoint
        if self.token:
            success, user_data = self.test_api_endpoint(
                "GET /api/auth/me", 
                "GET",
                "auth/me",
                auth_required=True
            )
            if success:
                print(f"   User level: {user_data.get('level')}")
                print(f"   Balance: {user_data.get('balance_ton', 0)} TON")
                print(f"   Is Admin: {user_data.get('is_admin', False)}")

    def test_island_system(self):
        """Test TON Island functionality"""
        print("\n🏝️ Testing TON Island System...")
        
        # Test island data retrieval
        success, island_data = self.test_api_endpoint(
            "GET /api/island",
            "GET", 
            "island"
        )
        
        if success and island_data:
            cells = island_data.get("cells", [])
            stats = island_data.get("stats", {})
            print(f"   Island cells: {len(cells)}")
            print(f"   Owned cells: {stats.get('owned_cells', 0)}")
            print(f"   Available cells: {stats.get('available_cells', 0)}")
            print(f"   Businesses: {stats.get('businesses', 0)}")
            
            # Find an available cell for testing
            available_cell = None
            for cell in cells[:5]:  # Check first 5 cells
                if not cell.get("owner"):
                    available_cell = cell
                    break
            
            if available_cell and self.token:
                x, y = available_cell["x"], available_cell["y"]
                print(f"   Testing plot purchase at ({x}, {y})")
                
                # Try to buy plot (will likely fail due to insufficient funds, but tests the endpoint)
                success, purchase_result = self.test_api_endpoint(
                    f"POST /api/island/buy/{x}/{y}",
                    "POST",
                    f"island/buy/{x}/{y}",
                    expected_status=400,  # Expect 400 due to insufficient funds
                    auth_required=True
                )
        
        # Test business types/config
        success, config_data = self.test_api_endpoint(
            "GET /api/config",
            "GET",
            "config"
        )
        
        if success:
            businesses = config_data.get("businesses", {})
            print(f"   Available business types: {len(businesses)}")

    def test_business_management(self):
        """Test business management APIs"""
        print("\n🏢 Testing Business Management...")
        
        if not self.token:
            print("   ⚠️ Skipping business tests - no auth token")
            return
            
        # Test getting user's businesses
        success, businesses_data = self.test_api_endpoint(
            "GET /api/my/businesses",
            "GET",
            "my/businesses", 
            auth_required=True
        )
        
        if success:
            businesses = businesses_data.get("businesses", [])
            summary = businesses_data.get("summary", {})
            print(f"   User businesses: {len(businesses)}")
            print(f"   Total pending income: {summary.get('total_pending_income', 0)}")
            print(f"   Daily income: {summary.get('total_daily_income', 0)}")
            
            # If user has businesses, test business details
            if businesses:
                business = businesses[0]
                business_id = business.get("id")
                
                if business_id:
                    success, business_details = self.test_api_endpoint(
                        f"GET /api/business/{business_id}",
                        "GET",
                        f"business/{business_id}",
                        auth_required=True
                    )

    def test_patronage_system(self):
        """Test patronage system"""
        print("\n👑 Testing Patronage System...")
        
        # Test getting available patrons
        success, patrons_data = self.test_api_endpoint(
            "GET /api/patrons",
            "GET",
            "patrons"
        )
        
        if success:
            patrons = patrons_data.get("patrons", [])
            print(f"   Available patrons: {len(patrons)}")
            for patron in patrons[:3]:  # Show first 3
                print(f"     - {patron.get('type')} (Level {patron.get('level')})")

    def test_warehouse_system(self):
        """Test warehouse rental system"""
        print("\n📦 Testing Warehouse System...")
        
        # Test warehouse rentals
        success, rentals_data = self.test_api_endpoint(
            "GET /api/warehouses/rentals",
            "GET",
            "warehouses/rentals"
        )
        
        if success:
            rentals = rentals_data.get("rentals", [])
            print(f"   Available warehouse rentals: {len(rentals)}")

    def test_banking_system(self):
        """Test banking and withdrawal system"""
        print("\n🏦 Testing Banking System...")
        
        # Test available banks
        success, banks_data = self.test_api_endpoint(
            "GET /api/banks",
            "GET",
            "banks"
        )
        
        if success:
            banks = banks_data.get("banks", [])
            print(f"   Available banks: {len(banks)}")
        
        # Test withdrawal queue (requires auth)
        if self.token:
            success, withdrawals = self.test_api_endpoint(
                "GET /api/withdrawals/queue",
                "GET",
                "withdrawals/queue",
                auth_required=True
            )

    def test_leaderboard(self):
        """Test leaderboard functionality"""
        print("\n🏆 Testing Leaderboard...")
        
        success, leaderboard = self.test_api_endpoint(
            "GET /api/leaderboard",
            "GET",
            "leaderboard"
        )
        
        if success:
            players = leaderboard.get("players", [])
            print(f"   Players in leaderboard: {len(players)}")
            if players:
                top_player = players[0]
                print(f"   Top player: {top_player.get('username', 'Unknown')} - {top_player.get('balance_ton', 0)} TON")

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n⚡ Testing Admin Endpoints...")
        
        if not self.token:
            print("   ⚠️ Skipping admin tests - no auth token")
            return
            
        # Test admin stats (may fail if user is not admin)
        success, stats = self.test_api_endpoint(
            "GET /api/admin/stats",
            "GET",
            "admin/stats",
            expected_status=403,  # Expect 403 if not admin
            auth_required=True
        )
        
        if success:
            print("   ✅ User has admin access!")
        else:
            print("   ℹ️ User does not have admin access (expected)")

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive TON City Backend Testing")
        print(f"📡 Testing API: {self.api_url}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Core functionality tests
        self.test_maintenance_apis()
        self.test_auth_system()
        self.test_island_system()
        self.test_business_management()
        self.test_patronage_system()
        self.test_warehouse_system()
        self.test_banking_system()
        self.test_leaderboard()
        self.test_admin_endpoints()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failed in self.failed_tests:
                print(f"   • {failed['name']}: {failed['error']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(self.failed_tests),
            "success_rate": self.tests_passed/self.tests_run if self.tests_run > 0 else 0,
            "duration": duration,
            "failed_test_details": self.failed_tests,
            "all_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = TonCityBackendTester()
    results = tester.run_comprehensive_test()
    
    # Return appropriate exit code
    if results["success_rate"] > 0.8:  # 80% success rate threshold
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())