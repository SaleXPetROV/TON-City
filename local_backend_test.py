#!/usr/bin/env python3
"""
Local Backend Test for TON City Builder
Tests backend functionality locally and identifies routing issues
"""
import requests
import sys
import time
import json
from datetime import datetime

class LocalBackendTester:
    def __init__(self):
        self.local_api = "http://localhost:8001/api"
        self.public_api = "https://a6fe025d-8065-48a3-b1c3-46f7c53f601e.stage-preview.emergentagent.com/api"
        self.frontend_url = "https://a6fe025d-8065-48a3-b1c3-46f7c53f601e.stage-preview.emergentagent.com"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_result(self, test_name, success, error=None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed_tests.append({"name": test_name, "error": error})
            print(f"❌ {test_name} - {error}")

    def test_local_backend(self):
        """Test backend APIs locally"""
        print("\n🔧 Testing Local Backend APIs...")
        
        # Test maintenance status
        try:
            response = requests.get(f"{self.local_api}/maintenance-status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Local maintenance-status API", True)
                print(f"   Maintenance enabled: {data.get('enabled')}")
            else:
                self.log_result("Local maintenance-status API", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Local maintenance-status API", False, str(e))

        # Test config API
        try:
            response = requests.get(f"{self.local_api}/config", timeout=5)
            if response.status_code == 200:
                data = response.json()
                businesses = data.get("businesses", {})
                self.log_result("Local config API", True)
                print(f"   Available business types: {len(businesses)}")
            else:
                self.log_result("Local config API", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Local config API", False, str(e))

        # Test auth endpoint
        try:
            test_data = {
                "address": "0:1234567890123456789012345678901234567890123456789012345678901234",
                "username": f"test_user_{int(time.time())}",
                "language": "ru"
            }
            response = requests.post(f"{self.local_api}/auth/verify-wallet", 
                                   json=test_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("token"):
                    self.token = data["token"]
                    self.log_result("Local auth API", True)
                    print(f"   Auth token obtained for: {data.get('user', {}).get('username')}")
                else:
                    self.log_result("Local auth API", False, "No token in response")
            else:
                self.log_result("Local auth API", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Local auth API", False, str(e))

        # Test island API
        try:
            response = requests.get(f"{self.local_api}/island", timeout=5)
            if response.status_code == 200:
                data = response.json()
                cells = data.get("cells", [])
                stats = data.get("stats", {})
                self.log_result("Local island API", True)
                print(f"   Island cells: {len(cells)}, Owned: {stats.get('owned_cells', 0)}")
            else:
                self.log_result("Local island API", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Local island API", False, str(e))

    def test_public_routing(self):
        """Test public API routing"""
        print("\n🌐 Testing Public API Routing...")
        
        # Test public maintenance endpoint
        try:
            response = requests.get(f"{self.public_api}/maintenance-status", timeout=10)
            if response.status_code == 200:
                self.log_result("Public maintenance-status routing", True)
            else:
                self.log_result("Public maintenance-status routing", False, 
                               f"Status {response.status_code}: {response.text[:100]}")
        except Exception as e:
            self.log_result("Public maintenance-status routing", False, str(e))

        # Test public config endpoint
        try:
            response = requests.get(f"{self.public_api}/config", timeout=10)
            if response.status_code == 200:
                self.log_result("Public config routing", True)
            else:
                self.log_result("Public config routing", False, 
                               f"Status {response.status_code}: {response.text[:100]}")
        except Exception as e:
            self.log_result("Public config routing", False, str(e))

    def test_frontend_loading(self):
        """Test if frontend loads"""
        print("\n🎨 Testing Frontend Loading...")
        
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                content = response.text
                if "TON City" in content or "ton-city" in content:
                    self.log_result("Frontend loads", True)
                    print(f"   Page size: {len(content)} chars")
                else:
                    self.log_result("Frontend loads", False, "No TON City content found")
            else:
                self.log_result("Frontend loads", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Frontend loads", False, str(e))

    def run_tests(self):
        """Run all tests"""
        print("🚀 TON City Builder - Local Backend Testing")
        print("=" * 50)
        
        self.test_local_backend()
        self.test_public_routing() 
        self.test_frontend_loading()
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   • {test['name']}: {test['error']}")
        
        # Return success if local backend works (even if public routing fails)
        return self.tests_passed >= 4  # At least basic local APIs should work

def main():
    tester = LocalBackendTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())