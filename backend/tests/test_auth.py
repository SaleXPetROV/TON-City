"""
Backend API Tests for TON City Builder Authentication
Tests: Registration, Login (email/username), /api/auth/me endpoint
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://authflow-ton.preview.emergentagent.com').rstrip('/')

# Test credentials from requirements
TEST_EMAIL = "test_p0_fix@example.com"
TEST_PASSWORD = "test123"
TEST_USERNAME = "testuser_p0"


class TestHealthCheck:
    """Health check tests - run first"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")


class TestUserRegistration:
    """User registration tests via /api/auth/register"""
    
    def test_register_new_user(self):
        """Test registering a new user with email/password/username"""
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            "email": f"TEST_user_{unique_id}@example.com",
            "password": "testpass123",
            "username": f"TEST_user_{unique_id}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Register response status: {response.status_code}")
        print(f"Register response: {response.text[:500]}")
        
        # Check status code
        if response.status_code == 400:
            # User might already exist - this is acceptable
            data = response.json()
            assert "уже" in data.get("detail", "").lower() or "already" in data.get("detail", "").lower()
            print(f"✓ Registration blocked for existing user: {data.get('detail')}")
            return
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["email"] == test_data["email"]
        assert data["user"]["username"] == test_data["username"]
        print(f"✓ User registered successfully: {data['user']['username']}")
    
    def test_register_duplicate_email(self):
        """Test that duplicate email registration fails"""
        # First registration
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            "email": f"TEST_dup_{unique_id}@example.com",
            "password": "testpass123",
            "username": f"TEST_dup_{unique_id}"
        }
        
        # Register first time
        requests.post(f"{BASE_URL}/api/auth/register", json=test_data)
        
        # Try to register again with same email
        test_data["username"] = f"TEST_dup2_{unique_id}"  # Different username
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "email" in data.get("detail", "").lower() or "уже" in data.get("detail", "").lower()
        print(f"✓ Duplicate email correctly rejected: {data.get('detail')}")
    
    def test_register_duplicate_username(self):
        """Test that duplicate username registration fails"""
        unique_id = str(uuid.uuid4())[:8]
        test_data = {
            "email": f"TEST_dupuser_{unique_id}@example.com",
            "password": "testpass123",
            "username": f"TEST_dupuser_{unique_id}"
        }
        
        # Register first time
        requests.post(f"{BASE_URL}/api/auth/register", json=test_data)
        
        # Try to register again with same username
        test_data["email"] = f"TEST_dupuser2_{unique_id}@example.com"  # Different email
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "username" in data.get("detail", "").lower() or "занят" in data.get("detail", "").lower()
        print(f"✓ Duplicate username correctly rejected: {data.get('detail')}")


class TestUserLogin:
    """User login tests via /api/auth/login"""
    
    @pytest.fixture(autouse=True)
    def setup_test_user(self):
        """Ensure test user exists before login tests"""
        # Try to register the test user
        test_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": TEST_USERNAME
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_data)
        if response.status_code == 200:
            print(f"✓ Test user created: {TEST_USERNAME}")
        else:
            print(f"ℹ Test user may already exist: {response.status_code}")
    
    def test_login_with_email(self):
        """Test login with email and password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["email"] == TEST_EMAIL
        print(f"✓ Login with email successful: {data['user']['username']}")
        return data["token"]
    
    def test_login_with_username(self):
        """Test login with username instead of email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USERNAME, "password": TEST_PASSWORD},  # Using username in email field
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login with username response status: {response.status_code}")
        print(f"Login with username response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert data["user"]["username"] == TEST_USERNAME
        print(f"✓ Login with username successful: {data['user']['username']}")
    
    def test_login_wrong_password(self):
        """Test login with wrong password returns clear error message"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": "wrongpassword123"},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Wrong password response status: {response.status_code}")
        print(f"Wrong password response: {response.text}")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        # Check for clear error message (not technical error)
        error_msg = data.get("detail", "")
        assert error_msg, "Should have error detail"
        # Should NOT contain technical errors like "body stream already read"
        assert "body stream" not in error_msg.lower(), f"Technical error exposed: {error_msg}"
        assert "already read" not in error_msg.lower(), f"Technical error exposed: {error_msg}"
        # Should contain user-friendly message
        assert "неверн" in error_msg.lower() or "invalid" in error_msg.lower() or "пароль" in error_msg.lower()
        print(f"✓ Wrong password returns clear error: {error_msg}")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nonexistent_user_12345@example.com", "password": "anypassword"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 401
        data = response.json()
        error_msg = data.get("detail", "")
        assert "body stream" not in error_msg.lower(), f"Technical error exposed: {error_msg}"
        print(f"✓ Non-existent user returns clear error: {error_msg}")


class TestAuthMe:
    """Tests for /api/auth/me endpoint"""
    
    def get_valid_token(self):
        """Helper to get a valid token"""
        # First ensure user exists
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "username": TEST_USERNAME
        })
        
        # Login to get token
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_auth_me_with_valid_token(self):
        """Test /api/auth/me returns user data with valid token"""
        token = self.get_valid_token()
        assert token, "Failed to get valid token"
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Auth/me response status: {response.status_code}")
        print(f"Auth/me response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain user id"
        assert "username" in data, "Response should contain username"
        assert "email" in data, "Response should contain email"
        assert data["email"] == TEST_EMAIL
        print(f"✓ Auth/me returns user data: {data['username']}")
    
    def test_auth_me_without_token(self):
        """Test /api/auth/me returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401
        print(f"✓ Auth/me without token returns 401")
    
    def test_auth_me_with_invalid_token(self):
        """Test /api/auth/me returns 401 with invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401
        print(f"✓ Auth/me with invalid token returns 401")


class TestStatsEndpoint:
    """Test public stats endpoint"""
    
    def test_stats_endpoint(self):
        """Test /api/stats returns game statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Stats endpoint works: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
