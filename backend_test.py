#!/usr/bin/env python3
"""
Backend Testing Suite for Admin Authentication System
Tests the admin login functionality with default credentials admin/admin
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001/api"
TEST_RESULTS = []

def log_test(test_name, status, message="", details=None):
    """Log test results"""
    result = {
        "test": test_name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    TEST_RESULTS.append(result)
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_symbol} {test_name}: {message}")
    if details:
        print(f"   Details: {details}")

def make_request(method, endpoint, data=None, headers=None, files=None):
    """Make HTTP request with error handling"""
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, headers=headers, files=files, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.exceptions.RequestException as e:
        return None

def test_health_check():
    """Test if backend is running"""
    response = make_request("GET", "/health")
    if response and response.status_code == 200:
        log_test("Backend Health Check", "PASS", "Backend is running and healthy")
        return True
    else:
        log_test("Backend Health Check", "FAIL", "Backend is not responding")
        return False

def test_default_admin_login():
    """Test login with default admin/admin credentials"""
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    response = make_request("POST", "/login", login_data)
    
    if not response:
        log_test("Default Admin Login", "FAIL", "No response from login endpoint")
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            if "access_token" in data and "must_change_password" in data:
                log_test("Default Admin Login", "PASS", 
                        f"Login successful, must_change_password: {data['must_change_password']}")
                return data["access_token"]
            else:
                log_test("Default Admin Login", "FAIL", 
                        "Login response missing required fields", data)
                return None
        except json.JSONDecodeError:
            log_test("Default Admin Login", "FAIL", "Invalid JSON response")
            return None
    else:
        try:
            error_data = response.json()
            log_test("Default Admin Login", "FAIL", 
                    f"Login failed with status {response.status_code}", error_data)
        except:
            log_test("Default Admin Login", "FAIL", 
                    f"Login failed with status {response.status_code}")
        return None

def test_me_endpoint(token):
    """Test /me endpoint to verify user info and password change requirement"""
    if not token:
        log_test("Me Endpoint Test", "SKIP", "No token available")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request("GET", "/me", headers=headers)
    
    if not response:
        log_test("Me Endpoint Test", "FAIL", "No response from /me endpoint")
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            required_fields = ["id", "username", "email", "must_change_password", "is_owner"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                log_test("Me Endpoint Test", "FAIL", 
                        f"Missing required fields: {missing_fields}", data)
                return None
            
            log_test("Me Endpoint Test", "PASS", 
                    f"User info retrieved - username: {data['username']}, must_change_password: {data['must_change_password']}, is_owner: {data['is_owner']}")
            return data
        except json.JSONDecodeError:
            log_test("Me Endpoint Test", "FAIL", "Invalid JSON response")
            return None
    else:
        log_test("Me Endpoint Test", "FAIL", f"Request failed with status {response.status_code}")
        return None

def test_change_credentials(token):
    """Test changing default credentials"""
    if not token:
        log_test("Change Credentials Test", "SKIP", "No token available")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test changing credentials using form data
    change_data = {
        "username": "newadmin",
        "password": "newpassword123"
    }
    
    response = make_request("POST", "/change-credentials", change_data, headers)
    
    if not response:
        log_test("Change Credentials Test", "FAIL", "No response from change-credentials endpoint")
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            if "access_token" in data and "must_change_password" in data:
                if data["must_change_password"] == False:
                    log_test("Change Credentials Test", "PASS", 
                            "Credentials changed successfully, must_change_password set to False")
                    return data["access_token"]
                else:
                    log_test("Change Credentials Test", "FAIL", 
                            "Credentials changed but must_change_password still True", data)
                    return None
            else:
                log_test("Change Credentials Test", "FAIL", 
                        "Response missing required fields", data)
                return None
        except json.JSONDecodeError:
            log_test("Change Credentials Test", "FAIL", "Invalid JSON response")
            return None
    else:
        try:
            error_data = response.json()
            log_test("Change Credentials Test", "FAIL", 
                    f"Request failed with status {response.status_code}", error_data)
        except:
            log_test("Change Credentials Test", "FAIL", 
                    f"Request failed with status {response.status_code}")
        return None

def test_new_credentials_login():
    """Test login with new credentials"""
    login_data = {
        "username": "newadmin",
        "password": "newpassword123"
    }
    
    response = make_request("POST", "/login", login_data)
    
    if not response:
        log_test("New Credentials Login", "FAIL", "No response from login endpoint")
        return None
    
    if response.status_code == 200:
        try:
            data = response.json()
            if "access_token" in data and "must_change_password" in data:
                if data["must_change_password"] == False:
                    log_test("New Credentials Login", "PASS", 
                            "Login with new credentials successful, no password change required")
                    return data["access_token"]
                else:
                    log_test("New Credentials Login", "WARN", 
                            "Login successful but still requires password change", data)
                    return data["access_token"]
            else:
                log_test("New Credentials Login", "FAIL", 
                        "Login response missing required fields", data)
                return None
        except json.JSONDecodeError:
            log_test("New Credentials Login", "FAIL", "Invalid JSON response")
            return None
    else:
        log_test("New Credentials Login", "FAIL", f"Login failed with status {response.status_code}")
        return None

def test_old_credentials_rejected():
    """Test that old admin/admin credentials are rejected after change"""
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    response = make_request("POST", "/login", login_data)
    
    if not response:
        log_test("Old Credentials Rejection", "FAIL", "No response from login endpoint")
        return False
    
    if response.status_code == 401:
        log_test("Old Credentials Rejection", "PASS", "Old admin/admin credentials properly rejected")
        return True
    elif response.status_code == 200:
        log_test("Old Credentials Rejection", "FAIL", "Old credentials still accepted - security issue!")
        return False
    else:
        log_test("Old Credentials Rejection", "WARN", f"Unexpected status code: {response.status_code}")
        return False

def test_invalid_credentials():
    """Test login with invalid credentials"""
    login_data = {
        "username": "invalid",
        "password": "invalid"
    }
    
    response = make_request("POST", "/login", login_data)
    
    if not response:
        log_test("Invalid Credentials Test", "FAIL", "No response from login endpoint")
        return False
    
    if response.status_code == 401:
        log_test("Invalid Credentials Test", "PASS", "Invalid credentials properly rejected")
        return True
    else:
        log_test("Invalid Credentials Test", "FAIL", f"Expected 401, got {response.status_code}")
        return False

def test_token_validation(token):
    """Test token validation with protected endpoint"""
    if not token:
        log_test("Token Validation Test", "SKIP", "No token available")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = make_request("GET", "/settings", headers=headers)
    
    if not response:
        log_test("Token Validation Test", "FAIL", "No response from protected endpoint")
        return False
    
    if response.status_code == 200:
        log_test("Token Validation Test", "PASS", "Token validation successful")
        return True
    else:
        log_test("Token Validation Test", "FAIL", f"Token validation failed with status {response.status_code}")
        return False

def run_admin_authentication_tests():
    """Run complete admin authentication test suite"""
    print("=" * 60)
    print("ADMIN AUTHENTICATION SYSTEM TESTING")
    print("=" * 60)
    print(f"Testing against: {BACKEND_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Backend is not running. Cannot proceed with tests.")
        return False
    
    print("\n🔐 TESTING DEFAULT ADMIN LOGIN FLOW")
    print("-" * 40)
    
    # Test 2: Default admin login
    initial_token = test_default_admin_login()
    
    # Test 3: Me endpoint with initial token
    user_info = test_me_endpoint(initial_token)
    
    # Test 4: Change credentials
    new_token = test_change_credentials(initial_token)
    
    # Test 5: Login with new credentials
    final_token = test_new_credentials_login()
    
    # Test 6: Verify old credentials are rejected
    test_old_credentials_rejected()
    
    print("\n🔒 TESTING SECURITY MEASURES")
    print("-" * 40)
    
    # Test 7: Invalid credentials
    test_invalid_credentials()
    
    # Test 8: Token validation
    test_token_validation(final_token or new_token)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in TEST_RESULTS if result["status"] == "PASS")
    failed = sum(1 for result in TEST_RESULTS if result["status"] == "FAIL")
    warnings = sum(1 for result in TEST_RESULTS if result["status"] == "WARN")
    skipped = sum(1 for result in TEST_RESULTS if result["status"] == "SKIP")
    
    print(f"Total Tests: {len(TEST_RESULTS)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"⏭️  Skipped: {skipped}")
    
    success_rate = (passed / len(TEST_RESULTS)) * 100 if TEST_RESULTS else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in TEST_RESULTS:
            if result["status"] == "FAIL":
                print(f"  - {result['test']}: {result['message']}")
    
    if warnings > 0:
        print("\n⚠️  WARNINGS:")
        for result in TEST_RESULTS:
            if result["status"] == "WARN":
                print(f"  - {result['test']}: {result['message']}")
    
    print(f"\nTest completed at: {datetime.now().isoformat()}")
    
    # Return True if all critical tests passed
    critical_failures = [r for r in TEST_RESULTS if r["status"] == "FAIL" and "Health Check" not in r["test"]]
    return len(critical_failures) == 0

if __name__ == "__main__":
    success = run_admin_authentication_tests()
    sys.exit(0 if success else 1)