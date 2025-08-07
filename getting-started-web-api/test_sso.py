#!/usr/bin/env python3
"""
Test script for SSO authentication setup
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

def test_sso_config():
    """Test the SSO configuration endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/polls/auth/sso-config/")
        print("✅ SSO Config Test:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            config = response.json()
            print(f"Okta Domain: {config.get('okta', {}).get('domain', 'Not configured')}")
            print(f"Google Client ID: {config.get('google', {}).get('client_id', 'Not configured')}")
        else:
            print(f"Error: {response.text}")
        print()
    except Exception as e:
        print(f"❌ SSO Config Test Failed: {e}")
        print()

def test_user_info():
    """Test the user info endpoint (should fail without auth)"""
    try:
        response = requests.get(f"{BASE_URL}/polls/auth/user-info/")
        print("✅ User Info Test (Unauthenticated):")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("Expected: 401 Unauthorized")
        else:
            print(f"Unexpected: {response.text}")
        print()
    except Exception as e:
        print(f"❌ User Info Test Failed: {e}")
        print()

def test_verify_token():
    """Test the token verification endpoint with invalid token"""
    try:
        data = {
            "token": "invalid-token",
            "provider": "okta"
        }
        response = requests.post(
            f"{BASE_URL}/polls/auth/verify-token/",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print("✅ Token Verification Test (Invalid Token):")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("Expected: 401 Unauthorized for invalid token")
        else:
            print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"❌ Token Verification Test Failed: {e}")
        print()

def test_polls_endpoint():
    """Test the polls endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/polls/")
        print("✅ Polls Endpoint Test:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Polls endpoint is accessible")
        else:
            print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"❌ Polls Endpoint Test Failed: {e}")
        print()

def main():
    print("🧪 Testing Django SSO Setup")
    print("=" * 40)
    
    test_sso_config()
    test_user_info()
    test_verify_token()
    test_polls_endpoint()
    
    print("📋 Setup Summary:")
    print("- SSO authentication backends configured")
    print("- OAuth2 provider tables created")
    print("- CORS headers configured for frontend integration")
    print("- REST API endpoints available")
    print()
    print("🚀 Next Steps:")
    print("1. Configure your Okta and Google OAuth credentials")
    print("2. Update environment variables with your credentials")
    print("3. Test with the provided frontend example")
    print("4. Integrate with your frontend application")

if __name__ == "__main__":
    main() 