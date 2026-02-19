#!/usr/bin/env python3
"""
TON City Builder Backend Authentication Testing
Testing specific features: Registration, Login, Email verification, Wallet auth
"""

import requests
import sys
import json
from datetime import datetime
import random
import string

class TONCityAuthTester:
    def __init__(self):
        # Use the public backend URL from frontend .env
        self.base_url = "http://localhost:8001"
        self.api = f"{self.base_url}/api"
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Generate unique test data for each run
        timestamp = datetime.now().strftime("%H%M%S")
        self.test_email = f"test{timestamp}@example.com"
        self.test_username = f"testuser{timestamp}"
        self.test_password = "TestPass123!"
        
        print(f"🔐 Authentication Testing Started")
        print(f"📍 Backend URL: {self.base_url}")
        print(f"📍 API Base: {self.api}")
        print(f"📧 Test Email: {self.test_email}")
        print(f"👤 Test Username: {self.test_username}")
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

    def test_register_initiate(self):
        """Test POST /api/auth/register/initiate - registration with email verification"""
        print("\n" + "="*50)
        print("📝 TESTING REGISTRATION INITIATE")
        print("="*50)
        
        data = {
            "email": self.test_email,
            "username": self.test_username,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Registration Initiate",
            "POST",
            "auth/register/initiate",
            200,
            data
        )
        
        if success:
            status = response.get('status')
            message = response.get('message', '')
            print(f"   Status: {status}")
            print(f"   Message: {message}")
            
            # Check if SMTP is configured or not
            if status == 'verification_sent':
                print("✅ Email verification required (SMTP configured)")
                return True, 'verification_needed'
            elif status == 'registered' and response.get('token'):
                print("✅ Registration completed immediately (SMTP not configured)")
                self.token = response['token']
                return True, 'registered_immediately'
            else:
                print(f"⚠️ Unexpected response: {response}")
                return False, None
        
        return False, None

    def test_register_verify(self):
        """Test POST /api/auth/register/verify - email code confirmation"""
        print("\n" + "="*50)
        print("✉️ TESTING EMAIL VERIFICATION")
        print("="*50)
        
        # Generate a dummy verification code for testing
        dummy_code = "123456"
        
        data = {
            "email": self.test_email,
            "code": dummy_code
        }
        
        success, response = self.run_test(
            "Email Code Verification",
            "POST",
            "auth/register/verify",
            [200, 400],  # 400 is expected for invalid code
            data
        )
        
        if success:
            if response.get('token'):
                print("✅ Verification successful (if code was valid)")
                self.token = response['token']
                return True
            elif response.get('detail') and 'код' in response.get('detail', '').lower():
                print("✅ Verification endpoint working (invalid code response)")
                return True
        
        return success

    def test_register_legacy(self):
        """Test POST /api/auth/register - backward compatibility"""
        print("\n" + "="*50)
        print("🔄 TESTING LEGACY REGISTRATION")
        print("="*50)
        
        # Use different email/username for legacy test
        timestamp = datetime.now().strftime("%H%M%S") + "2"
        legacy_email = f"legacy{timestamp}@example.com"
        legacy_username = f"legacy{timestamp}"
        
        data = {
            "email": legacy_email,
            "username": legacy_username,
            "password": self.test_password
        }
        
        success, response = self.run_test(
            "Legacy Registration",
            "POST",
            "auth/register",
            200,
            data
        )
        
        if success and response.get('token'):
            print("✅ Legacy registration working")
            user_info = response.get('user', {})
            print(f"   Username: {user_info.get('username')}")
            print(f"   Email Verified: {user_info.get('email_verified', 'N/A')}")
            return True
        
        return success

    def test_login(self):
        """Test POST /api/auth/login - email/password login"""
        print("\n" + "="*50)
        print("🔑 TESTING LOGIN")
        print("="*50)
        
        # First test admin credentials
        admin_credentials = {
            "email": "admin@toncity.com",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            admin_credentials
        )
        
        if success and response.get('token'):
            self.admin_token = response['token']
            user_info = response.get('user', {})
            print(f"   Username: {user_info.get('username')}")
            print(f"   Email: {user_info.get('email')}")
            print(f"   Admin: {user_info.get('is_admin', False)}")
            print("✅ Admin login successful")
            
            # Test login with username instead of email
            if user_info.get('username'):
                username_login = {
                    "email": user_info.get('username'),  # Using username in email field
                    "password": "admin123"
                }
                
                success2, response2 = self.run_test(
                    "Login with Username",
                    "POST",
                    "auth/login",
                    200,
                    username_login
                )
                
                if success2:
                    print("✅ Username login also working")
                    return True
            
            return True
        
        # Test invalid credentials
        invalid_credentials = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        
        success3, response3 = self.run_test(
            "Invalid Login (Expected to fail)",
            "POST",
            "auth/login",
            401,
            invalid_credentials
        )
        
        if success3:
            print("✅ Invalid credentials properly rejected")
        
        return success or success3

    def test_verify_wallet(self):
        """Test POST /api/auth/verify-wallet - wallet authorization"""
        print("\n" + "="*50)
        print("💰 TESTING WALLET VERIFICATION")
        print("="*50)
        
        # Generate a dummy TON wallet address for testing
        dummy_wallet = "EQDtFpEwcFAEcRe5mLVh2N6C0x-_hJEM7W61_JLnSF8C4EAD"
        
        data = {
            "address": dummy_wallet,
            "language": "ru",
            "username": f"wallet_{datetime.now().strftime('%H%M%S')}",
            "email": "",
            "password": ""
        }
        
        success, response = self.run_test(
            "Wallet Verification",
            "POST",
            "auth/verify-wallet",
            200,
            data
        )
        
        if success:
            status = response.get('status')
            print(f"   Status: {status}")
            
            if status == 'need_username':
                print("✅ New wallet requires username (correct flow)")
                return True
            elif status == 'ok' and response.get('token'):
                print("✅ Existing wallet authenticated successfully")
                return True
            elif response.get('token'):
                print("✅ Wallet verification successful with token")
                return True
        
        return success

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
                print(f"   Email: {response.get('email', 'N/A')}")
                print(f"   Admin: {response.get('is_admin', False)}")
                print(f"   Auth Type: {response.get('auth_type', 'unknown')}")
                print(f"   Wallet: {response.get('wallet_address', 'N/A')}")
                return True
        
        return False

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n" + "="*50)
        print("⚠️ TESTING ERROR HANDLING")
        print("="*50)
        
        results = []
        
        # Test registration with existing email
        existing_email_data = {
            "email": self.test_email,  # Same email as before
            "username": "newuser123",
            "password": self.test_password
        }
        
        success1, response1 = self.run_test(
            "Duplicate Email Registration",
            "POST",
            "auth/register/initiate",
            400,  # Should fail
            existing_email_data
        )
        
        if success1:
            print("✅ Duplicate email properly rejected")
            results.append(True)
        else:
            results.append(False)
        
        # Test invalid email verification
        invalid_verify_data = {
            "email": "nonexistent@test.com",
            "code": "123456"
        }
        
        success2, response2 = self.run_test(
            "Invalid Email Verification",
            "POST",
            "auth/register/verify",
            400,  # Should fail
            invalid_verify_data
        )
        
        if success2:
            print("✅ Invalid verification properly handled")
            results.append(True)
        else:
            results.append(False)
        
        # Test short password
        short_password_data = {
            "email": "test@short.com",
            "username": "testshort",
            "password": "123"  # Too short
        }
        
        success3, response3 = self.run_test(
            "Short Password Registration",
            "POST",
            "auth/register/initiate",
            400,  # Should fail
            short_password_data
        )
        
        if success3:
            print("✅ Short password properly rejected")
            results.append(True)
        else:
            results.append(False)
            
        return all(results)

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 TON City Builder Authentication Test Suite")
        print("="*60)
        
        test_results = []
        
        # Test registration initiate
        result1, reg_status = self.test_register_initiate()
        test_results.append(result1)
        
        # Test email verification (if needed)
        if reg_status == 'verification_needed':
            result2 = self.test_register_verify()
            test_results.append(result2)
        
        # Test legacy registration
        result3 = self.test_register_legacy()
        test_results.append(result3)
        
        # Test login functionality
        result4 = self.test_login()
        test_results.append(result4)
        
        # Test wallet verification
        result5 = self.test_verify_wallet()
        test_results.append(result5)
        
        # Test auth/me endpoint
        result6 = self.test_auth_me_endpoint()
        test_results.append(result6)
        
        # Test error handling
        result7 = self.test_error_handling()
        test_results.append(result7)
        
        # Print final results
        print("\n" + "="*60)
        print("📊 AUTHENTICATION TEST RESULTS")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL AUTHENTICATION TESTS PASSED!")
            return 0
        else:
            print(f"⚠️ {self.tests_run - self.tests_passed} TESTS FAILED")
            return 1

def main():
    tester = TONCityAuthTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())