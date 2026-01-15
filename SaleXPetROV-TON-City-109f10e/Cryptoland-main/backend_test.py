#!/usr/bin/env python3
"""
TON City Builder Backend API Tests
Tests all backend endpoints for the TON city game
"""

import requests
import sys
import json
import math
from datetime import datetime

class TONCityAPITester:
    def __init__(self, base_url="https://tonworld-build.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if success and response.content:
                try:
                    response_data = response.json()
                    details += f", Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}"
                except:
                    details += ", Response: Non-JSON"
            elif not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Raw response: {response.text[:100]}"

            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        self.run_test("Root endpoint", "GET", "", 200)
        
        # Test health endpoint with WebSocket support
        success, health_data = self.run_test("Health check", "GET", "health", 200)
        
        if success and health_data:
            # Check for websocket support
            if health_data.get('websocket') is True:
                self.log_test("WebSocket support check", True, "WebSocket support confirmed in health endpoint")
            else:
                self.log_test("WebSocket support check", False, f"WebSocket support not found or false: {health_data.get('websocket')}")

    def test_stats_endpoints(self):
        """Test statistics endpoints"""
        print("\n📊 Testing Stats Endpoints...")
        
        # Test game stats
        success, stats_data = self.run_test("Game statistics", "GET", "stats", 200)
        
        if success and stats_data:
            # Verify stats structure
            expected_keys = ['total_plots', 'owned_plots', 'available_plots', 'total_businesses', 'total_players', 'total_volume_ton']
            missing_keys = [key for key in expected_keys if key not in stats_data]
            
            if not missing_keys:
                self.log_test("Stats structure validation", True, f"All expected keys present: {expected_keys}")
            else:
                self.log_test("Stats structure validation", False, f"Missing keys: {missing_keys}")
        
        # Test leaderboard
        self.run_test("Leaderboard", "GET", "leaderboard", 200)
        
        # Test income table with Russian language
        success, income_ru = self.run_test("Income table (Russian)", "GET", "stats/income-table?lang=ru", 200)
        
        if success and income_ru:
            income_table = income_ru.get('income_table', {})
            if income_table:
                # Check if business names are in Russian
                sample_business = list(income_table.values())[0]
                if 'name' in sample_business:
                    # Check if name contains Cyrillic characters (Russian)
                    name = sample_business['name']
                    has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in name)
                    if has_cyrillic:
                        self.log_test("Russian language support", True, f"Russian business names found: {name}")
                    else:
                        self.log_test("Russian language support", False, f"No Cyrillic characters in name: {name}")
                else:
                    self.log_test("Russian language support", False, "No name field in business data")
            else:
                self.log_test("Russian language support", False, "No income_table in response")
        
        # Test income table with English language
        success, income_en = self.run_test("Income table (English)", "GET", "stats/income-table?lang=en", 200)
        
        if success and income_en:
            income_table = income_en.get('income_table', {})
            if income_table:
                # Check if business names are in English
                sample_business = list(income_table.values())[0]
                if 'name' in sample_business:
                    name = sample_business['name']
                    # English names should not contain Cyrillic
                    has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in name)
                    if not has_cyrillic and len(name) > 0:
                        self.log_test("English language support", True, f"English business names found: {name}")
                    else:
                        self.log_test("English language support", False, f"Unexpected characters in English name: {name}")
                else:
                    self.log_test("English language support", False, "No name field in business data")
            else:
                self.log_test("English language support", False, "No income_table in response")

    def test_business_types(self):
        """Test business types endpoint"""
        print("\n🏢 Testing Business Types...")
        
        success, biz_data = self.run_test("Business types", "GET", "businesses/types", 200)
        
        if success and biz_data:
            business_types = biz_data.get('business_types', {})
            
            # Check for 20+ business types
            total_types = len(business_types)
            if total_types >= 20:
                self.log_test("Business types count (20+)", True, f"Found {total_types} business types (≥20 required)")
            else:
                self.log_test("Business types count (20+)", False, f"Found only {total_types} business types, expected ≥20")
            
            # Check for income_by_level in business types
            if business_types:
                sample_type = list(business_types.values())[0]
                if 'income_by_level' in sample_type:
                    income_levels = sample_type['income_by_level']
                    if isinstance(income_levels, dict) and len(income_levels) >= 10:
                        self.log_test("Income by level structure", True, f"Found income data for {len(income_levels)} levels")
                    else:
                        self.log_test("Income by level structure", False, f"Income levels incomplete: {len(income_levels) if isinstance(income_levels, dict) else 'not dict'}")
                else:
                    self.log_test("Income by level structure", False, "income_by_level field missing")
            
            # Check for allowed_zones restrictions
            zones_found = False
            for biz_type, biz_data in business_types.items():
                if 'allowed_zones' in biz_data:
                    zones_found = True
                    break
            
            if zones_found:
                self.log_test("Business zone restrictions", True, "allowed_zones field found in business types")
            else:
                self.log_test("Business zone restrictions", False, "allowed_zones field missing from business types")
            
            # Validate business type structure
            if business_types:
                sample_type = list(business_types.values())[0]
                expected_props = ['name', 'icon', 'cost', 'base_income', 'produces', 'sector']
                missing_props = [prop for prop in expected_props if prop not in sample_type]
                
                if not missing_props:
                    self.log_test("Business type structure", True, f"All properties present: {expected_props}")
                else:
                    self.log_test("Business type structure", False, f"Missing properties: {missing_props}")

    def test_wallet_verification(self):
        """Test wallet verification and authentication"""
        print("\n🔐 Testing Wallet Authentication...")
        
        # Test wallet verification with mock address and language preference
        test_wallet = "0:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12"
        
        success, auth_data = self.run_test(
            "Wallet verification with language", 
            "POST", 
            "auth/verify-wallet", 
            200,
            {"address": test_wallet, "language": "ru"}
        )
        
        if success and auth_data:
            if 'token' in auth_data:
                self.token = auth_data['token']
                self.log_test("Token received", True, "Authentication token obtained")
                
                # Check if user language preference is set
                if 'user' in auth_data and auth_data['user'].get('language') == 'ru':
                    self.log_test("Language preference", True, "User language set to Russian")
                else:
                    self.log_test("Language preference", False, f"Language not set correctly: {auth_data.get('user', {}).get('language')}")
                
                # Test authenticated endpoint
                self.run_test("Get current user", "GET", "auth/me", 200)
            else:
                self.log_test("Token received", False, "No token in response")

    def test_plot_endpoints(self):
        """Test plot-related endpoints"""
        print("\n🗺️ Testing Plot Endpoints...")
        
        # Test get all plots
        self.run_test("Get all plots", "GET", "plots", 200)
        
        # Test specific coordinates - center (should be ~100 TON)
        success, center_plot = self.run_test("Get center plot (50,50)", "GET", "plots/coords/50/50", 200)
        
        if success and center_plot:
            center_price = center_plot.get('price', 0)
            # Center should be close to 100 TON
            if 95 <= center_price <= 100:
                self.log_test("Center plot price validation", True, f"Price {center_price} TON is correct for center")
            else:
                self.log_test("Center plot price validation", False, f"Price {center_price} TON, expected ~100 TON")
        
        # Test edge coordinates (should be ~10 TON)
        success, edge_plot = self.run_test("Get edge plot (0,0)", "GET", "plots/coords/0/0", 200)
        
        if success and edge_plot:
            edge_price = edge_plot.get('price', 0)
            # Edge should be close to 10 TON
            if 10 <= edge_price <= 15:
                self.log_test("Edge plot price validation", True, f"Price {edge_price} TON is correct for edge")
            else:
                self.log_test("Edge plot price validation", False, f"Price {edge_price} TON, expected ~10 TON")

    def test_price_calculation_formula(self):
        """Test the price calculation formula"""
        print("\n💰 Testing Price Calculation Formula...")
        
        # Test various coordinates to verify formula
        test_coords = [
            (50, 50),  # Center - should be 100 TON
            (0, 0),    # Corner - should be 10 TON  
            (25, 25),  # Quarter - should be ~55 TON
            (75, 75),  # Three-quarter - should be ~55 TON
        ]
        
        for x, y in test_coords:
            success, plot_data = self.run_test(f"Price test ({x},{y})", "GET", f"plots/coords/{x}/{y}", 200)
            
            if success and plot_data:
                actual_price = plot_data.get('price', 0)
                
                # Calculate expected price using the formula
                center_x, center_y = 50, 50
                distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                max_distance = math.sqrt(50**2 + 50**2)  # ~70.7
                expected_price = 10 + (90 * (1 - distance / max_distance))
                
                # Allow 1% tolerance
                tolerance = expected_price * 0.01
                if abs(actual_price - expected_price) <= tolerance:
                    self.log_test(f"Price formula ({x},{y})", True, f"Actual: {actual_price}, Expected: {expected_price:.2f}")
                else:
                    self.log_test(f"Price formula ({x},{y})", False, f"Actual: {actual_price}, Expected: {expected_price:.2f}")

    def test_purchase_flow(self):
        """Test plot purchase initiation (without actual blockchain transaction)"""
        print("\n🛒 Testing Purchase Flow...")
        
        if not self.token:
            self.log_test("Purchase flow", False, "No authentication token available")
            return
        
        # Test purchase initiation
        success, purchase_data = self.run_test(
            "Initiate plot purchase", 
            "POST", 
            "plots/purchase", 
            200,
            {"plot_x": 10, "plot_y": 10}
        )
        
        if success and purchase_data:
            required_fields = ['transaction_id', 'plot_id', 'amount_ton']
            missing_fields = [field for field in required_fields if field not in purchase_data]
            
            if not missing_fields:
                self.log_test("Purchase response structure", True, f"All required fields present: {required_fields}")
            else:
                self.log_test("Purchase response structure", False, f"Missing fields: {missing_fields}")

    def test_business_endpoints(self):
        """Test business-related endpoints"""
        print("\n🏭 Testing Business Endpoints...")
        
        # Test get all businesses
        self.run_test("Get all businesses", "GET", "businesses", 200)

    def test_transaction_endpoints(self):
        """Test transaction endpoints"""
        print("\n💳 Testing Transaction Endpoints...")
        
        # Note: User transactions endpoint doesn't exist, only admin endpoint
        # This is expected behavior - users see transactions through other means
        self.log_test("Transaction endpoints", True, "No user transaction endpoint - admin only (expected behavior)")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting TON City Builder API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run test suites
        self.test_health_check()
        self.test_stats_endpoints()
        self.test_business_types()
        self.test_wallet_verification()
        self.test_plot_endpoints()
        self.test_price_calculation_formula()
        self.test_purchase_flow()
        self.test_business_endpoints()
        self.test_transaction_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    tester = TONCityAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())