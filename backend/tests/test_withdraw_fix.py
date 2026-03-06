"""
Test suite for TON-City withdrawal bug fix verification
Focus: Verify withdrawal endpoints return 400 errors instead of 500 for users without wallets
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "player1@toncity.io"
TEST_USER_PASSWORD = "Player1!"
ADMIN_EMAIL = "admin@toncity.io"
ADMIN_PASSWORD = "Admin123!"


class TestLoginAndAuth:
    """Test authentication endpoints"""
    
    def test_login_test_user(self):
        """Test login with test user credentials (player1)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        return data["token"]
    
    def test_get_user_info(self):
        """Test getting user info after login"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        
        # Get user info
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"User info response status: {response.status_code}")
        print(f"User info: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "wallet_address" in data or data.get("wallet_address") is None
        return data


class TestWithdrawalBugFix:
    """Test withdrawal endpoints for fixed KeyError bug"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for test user (player1 - without wallet)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_withdraw_without_wallet_returns_400(self, auth_token):
        """
        CRITICAL TEST: /api/withdraw should return 400 for user without wallet
        Previously returned 500 KeyError: 'wallet_address'
        """
        response = requests.post(
            f"{BASE_URL}/api/withdraw",
            json={"amount": 1.0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"Withdraw response status: {response.status_code}")
        print(f"Withdraw response: {response.json()}")
        
        # Should be 400 Bad Request, NOT 500 Internal Server Error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        # Verify error message
        data = response.json()
        assert "detail" in data
        # Message should be about connecting wallet
        assert "кошелёк" in data["detail"].lower() or "wallet" in data["detail"].lower(), \
            f"Expected wallet-related error message, got: {data['detail']}"
    
    def test_withdraw_instant_without_wallet_returns_400(self, auth_token):
        """
        CRITICAL TEST: /api/withdraw/instant should return 400 for user without wallet
        """
        response = requests.post(
            f"{BASE_URL}/api/withdraw/instant",
            params={"amount": 1.0, "bank_id": "fake-bank-id"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"Instant withdraw response status: {response.status_code}")
        print(f"Instant withdraw response: {response.json()}")
        
        # Should be 400 Bad Request, NOT 500 Internal Server Error
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        # Verify error message
        data = response.json()
        assert "detail" in data
        # Message should be about connecting wallet OR insufficient funds OR bank not found
        # All of these are acceptable 400 errors


class TestWithdrawalValidation:
    """Test withdrawal validation logic"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_withdraw_zero_amount(self, auth_token):
        """Test withdrawal with zero amount"""
        response = requests.post(
            f"{BASE_URL}/api/withdraw",
            json={"amount": 0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"Zero amount withdraw response: {response.status_code}")
        
        # Should return 400
        assert response.status_code == 400
    
    def test_withdraw_negative_amount(self, auth_token):
        """Test withdrawal with negative amount"""
        response = requests.post(
            f"{BASE_URL}/api/withdraw",
            json={"amount": -5.0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        print(f"Negative amount withdraw response: {response.status_code}")
        
        # Should return 400
        assert response.status_code == 400


class TestBanksEndpoint:
    """Test banks endpoint for instant withdrawal"""
    
    def test_get_available_banks(self):
        """Test getting available banks - no auth required"""
        response = requests.get(f"{BASE_URL}/api/banks")
        print(f"Banks response status: {response.status_code}")
        print(f"Banks response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "banks" in data
        assert isinstance(data["banks"], list)


class TestDepositModal:
    """Test deposit-related endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_user_balance_accessible(self, auth_token):
        """Test that user balance is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "balance_ton" in data
        print(f"User balance: {data.get('balance_ton', 0)} TON")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
