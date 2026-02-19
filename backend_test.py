#!/usr/bin/env python3
"""
TON City Builder Backend API Testing
Testing specific features: Mobile adaptation, Buildings toggle, Maintenance mode, Admin navigation
"""

import requests
import sys
import json
from datetime import datetime

class TONCityBackendTester:
    def __init__(self):
        # Use the public backend URL from frontend .env
        self.base_url = "https://readme-update-2.preview.emergentagent.com"
        self.api = f"{self.base_url}/api"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔧 Backend Testing Started")
        print(f"📍 Backend URL: {self.base_url}")
        print(f"📍 API Base: {self.api}")
        print("-" * 60)

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api}/{endpoint}" if not endpoint.startswith('http') else endpoint
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=default_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=default_headers)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED")
                try:
                    json_response = response.json()
                    print(f"   Response: {json.dumps(json_response, indent=2)[:200]}...")
                    return True, json_response
                except:
                    print(f"   Response (text): {response.text[:100]}...")
                    return True, response.text
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_maintenance_status_api(self):
        """Test GET /api/maintenance-status - Required for MaintenanceOverlay"""
        print("\n" + "="*50)
        print("🔧 TESTING MAINTENANCE API")
        print("="*50)
        
        success, response = self.run_test(
            "Maintenance Status Check",
            "GET", 
            "maintenance-status",
            200
        )
        
        if success:
            enabled = response.get('enabled', None)
            print(f"   Maintenance Status: {'ENABLED' if enabled else 'DISABLED'}")
            if enabled is False:
                print("✅ Maintenance correctly disabled for normal operation")
            return success
        return False

    def test_admin_login(self):
        """Test admin login with provided credentials"""
        print("\n" + "="*50)
        print("👤 TESTING ADMIN LOGIN")
        print("="*50)
        
        # Test admin login - trying different endpoints
        admin_credentials = {
            "email": "admin@toncity.com",
            "password": "admin123"
        }
        
        # Try email login first
        success, response = self.run_test(
            "Admin Email Login",
            "POST",
            "auth/login",
            200,
            admin_credentials
        )
        
        if success and response.get('token'):
            self.admin_token = response['token']
            user_info = response.get('user', {})
            is_admin = user_info.get('is_admin', False)
            print(f"   Admin Status: {'YES' if is_admin else 'NO'}")
            if is_admin:
                print("✅ Admin login successful with correct privileges")
                return True
            else:
                print("⚠️ Login successful but admin privileges not found")
        
        # Also try wallet verification if email login didn't work
        if not self.admin_token:
            success2, response2 = self.run_test(
                "Admin Wallet Verification Fallback", 
                "POST",
                "auth/verify-wallet",
                200,
                {
                    "address": "admin@toncity.com",
                    "username": "admin", 
                    "email": "admin@toncity.com",
                    "password": "admin123"
                }
            )
            if success2 and response2.get('token'):
                self.admin_token = response2['token']
                return True
        
        return success

    def test_admin_maintenance_endpoints(self):
        """Test admin maintenance control endpoints"""
        print("\n" + "="*50)
        print("🔧 TESTING ADMIN MAINTENANCE CONTROL")
        print("="*50)
        
        if not self.admin_token:
            print("❌ No admin token available - skipping admin tests")
            return False
        
        # Test GET admin maintenance status
        success1, response1 = self.run_test(
            "Admin Maintenance Status",
            "GET",
            "admin/maintenance",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success1:
            current_status = response1.get('enabled', False)
            print(f"   Current Status: {'ON' if current_status else 'OFF'}")
        
        # Test POST admin maintenance toggle
        success2, response2 = self.run_test(
            "Admin Maintenance Toggle",
            "POST",
            "admin/maintenance",
            200,
            {"enabled": False},  # Ensure it's disabled for testing
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success2:
            print("✅ Admin can control maintenance mode")
        
        return success1 and success2

    def test_auth_me_endpoint(self):
        """Test /auth/me endpoint for user info"""
        print("\n" + "="*50)
        print("👤 TESTING AUTH/ME ENDPOINT")
        print("="*50)
        
        if self.admin_token:
            success, response = self.run_test(
                "Auth Me (Admin Token)",
                "GET",
                "auth/me",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   Username: {response.get('username', 'N/A')}")
                print(f"   Admin: {response.get('is_admin', False)}")
                print(f"   Auth Type: {response.get('auth_type', 'unknown')}")
                return True
        
        return False

    def test_core_apis_for_frontend(self):
        """Test core APIs that frontend needs to load"""
        print("\n" + "="*50)
        print("🏗️ TESTING CORE APIS FOR FRONTEND")
        print("="*50)
        
        results = []
        
        # Test config endpoint
        success1, config = self.run_test(
            "App Configuration",
            "GET",
            "config", 
            200
        )
        if success1:
            businesses = config.get('businesses', {})
            print(f"   Business Types: {len(businesses)}")
            results.append(True)
        else:
            results.append(False)
        
        # Test island endpoint  
        success2, island = self.run_test(
            "Island Data",
            "GET",
            "island",
            200
        )
        if success2:
            cells = island.get('cells', [])
            print(f"   Island Cells: {len(cells)}")
            results.append(True)
        else:
            results.append(False)
        
        return all(results)

    def test_businesses_types_endpoint(self):
        """Test business types endpoint for buildings toggle functionality"""
        print("\n" + "="*50)
        print("🏢 TESTING BUSINESS TYPES API")
        print("="*50)
        
        success, response = self.run_test(
            "Business Types",
            "GET",
            "businesses/types",
            200
        )
        
        if success:
            # Response might be in different formats
            if isinstance(response, dict):
                if 'business_types' in response:
                    types = response['business_types']
                elif 'businesses' in response:
                    types = response['businesses'] 
                else:
                    types = response
            else:
                types = response
                
            print(f"   Available Business Types: {len(types) if isinstance(types, (dict, list)) else 'N/A'}")
            if isinstance(types, dict):
                for biz_type, config in list(types.items())[:3]:  # Show first 3
                    name = config.get('name', {}) if isinstance(config, dict) else biz_type
                    icon = config.get('icon', '🏢') if isinstance(config, dict) else '🏢'
                    print(f"     - {biz_type}: {icon} {name}")
            return True
        
        # Fallback: check if it's in config endpoint
        success2, config = self.run_test(
            "Business Types from Config",
            "GET", 
            "config",
            200
        )
        
        if success2:
            businesses = config.get('businesses', {})
            print(f"   Business Types (from config): {len(businesses)}")
            return True
            
        return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 TON City Builder Backend Test Suite")
        print("="*60)
        
        # Test maintenance API (critical for MaintenanceOverlay component)
        self.test_maintenance_status_api()
        
        # Test admin login
        self.test_admin_login()
        
        # Test admin maintenance control
        self.test_admin_maintenance_endpoints()
        
        # Test auth/me endpoint
        self.test_auth_me_endpoint()
        
        # Test core APIs 
        self.test_core_apis_for_frontend()
        
        # Test business types for buildings toggle
        self.test_businesses_types_endpoint()
        
        # Print final results
        print("\n" + "="*60)
        print("📊 BACKEND TEST RESULTS")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL BACKEND TESTS PASSED!")
            return 0
        else:
            print(f"⚠️ {self.tests_run - self.tests_passed} TESTS FAILED")
            return 1

def main():
    tester = TONCityBackendTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())