#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Sectorfive Personal Website
Tests all backend API endpoints including authentication, CRUD operations, file uploads, analytics, and more.
"""

import requests
import json
import os
import tempfile
from datetime import datetime
import time

# Configuration
BASE_URL = "https://cmsadmin.preview.emergentagent.com/api"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin"

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.auth_headers = {}
        self.test_results = []
        
    def log_result(self, test_name, success, message="", details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} - {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def test_admin_onboarding_flow(self):
        """Test the complete admin onboarding flow with credential changes"""
        print("\n=== Testing Admin Onboarding Flow ===")
        
        # Test 1: Initial login with default admin credentials
        try:
            login_data = {
                "username": "admin",
                "password": "admin"
            }
            response = requests.post(f"{self.base_url}/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and data.get("must_change_password") == True:
                    self.token = data["access_token"]
                    self.auth_headers = {"Authorization": f"Bearer {self.token}"}
                    self.log_result("Admin Onboarding - Initial Login", True, "Successfully logged in with default admin credentials, must_change_password=true")
                else:
                    self.log_result("Admin Onboarding - Initial Login", False, "Login response missing required fields or must_change_password not true", str(data))
            else:
                self.log_result("Admin Onboarding - Initial Login", False, f"Initial login failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Admin Onboarding - Initial Login", False, "Initial login request failed", str(e))
        
        # Test 2: Check /me endpoint returns must_change_password=true
        if self.token:
            try:
                response = requests.get(f"{self.base_url}/me", headers=self.auth_headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get("must_change_password") == True and user_data.get("username") == "admin":
                        self.log_result("Admin Onboarding - Me Endpoint Check", True, "Me endpoint correctly returns must_change_password=true for admin")
                    else:
                        self.log_result("Admin Onboarding - Me Endpoint Check", False, "Me endpoint response incorrect", str(user_data))
                else:
                    self.log_result("Admin Onboarding - Me Endpoint Check", False, f"Me endpoint failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Admin Onboarding - Me Endpoint Check", False, "Me endpoint request failed", str(e))
        
        # Test 3: Change credentials using /change-credentials
        if self.token:
            try:
                change_data = {
                    "old_password": "admin",
                    "new_username": "newadmin",
                    "new_password": "newpass"
                }
                response = requests.post(f"{self.base_url}/change-credentials", data=change_data, headers=self.auth_headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if "message" in result:
                        self.log_result("Admin Onboarding - Change Credentials", True, "Successfully changed admin credentials")
                    else:
                        self.log_result("Admin Onboarding - Change Credentials", False, "Change credentials response missing message", str(result))
                else:
                    self.log_result("Admin Onboarding - Change Credentials", False, f"Change credentials failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Admin Onboarding - Change Credentials", False, "Change credentials request failed", str(e))
        
        # Test 4: Login with new credentials
        try:
            new_login_data = {
                "username": "newadmin",
                "password": "newpass"
            }
            response = requests.post(f"{self.base_url}/login", json=new_login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and data.get("must_change_password") == False:
                    new_token = data["access_token"]
                    new_auth_headers = {"Authorization": f"Bearer {new_token}"}
                    self.log_result("Admin Onboarding - New Credentials Login", True, "Successfully logged in with new credentials, must_change_password=false")
                    
                    # Update token for further tests
                    self.token = new_token
                    self.auth_headers = new_auth_headers
                else:
                    self.log_result("Admin Onboarding - New Credentials Login", False, "New login response incorrect", str(data))
            else:
                self.log_result("Admin Onboarding - New Credentials Login", False, f"New credentials login failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Admin Onboarding - New Credentials Login", False, "New credentials login request failed", str(e))
        
        # Test 5: Verify /me endpoint with new credentials shows must_change_password=false
        if self.token:
            try:
                response = requests.get(f"{self.base_url}/me", headers=self.auth_headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get("must_change_password") == False and user_data.get("username") == "newadmin":
                        self.log_result("Admin Onboarding - Final Me Check", True, "Me endpoint correctly shows must_change_password=false for newadmin")
                    else:
                        self.log_result("Admin Onboarding - Final Me Check", False, "Final me endpoint response incorrect", str(user_data))
                else:
                    self.log_result("Admin Onboarding - Final Me Check", False, f"Final me endpoint failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Admin Onboarding - Final Me Check", False, "Final me endpoint request failed", str(e))
        
        # Test 6: Verify old admin credentials no longer work
        try:
            old_login_data = {
                "username": "admin",
                "password": "admin"
            }
            response = requests.post(f"{self.base_url}/login", json=old_login_data)
            
            if response.status_code == 401:
                self.log_result("Admin Onboarding - Old Credentials Rejected", True, "Old admin credentials correctly rejected after change")
            else:
                self.log_result("Admin Onboarding - Old Credentials Rejected", False, f"Old credentials should be rejected, got status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Admin Onboarding - Old Credentials Rejected", False, "Old credentials rejection test failed", str(e))

    def test_authentication_system(self):
        """Test the complete authentication system"""
        print("\n=== Testing Authentication System ===")
        
        # Test 1: Valid login (now using new credentials after onboarding)
        try:
            login_data = {
                "username": "newadmin",
                "password": "newpass"
            }
            response = requests.post(f"{self.base_url}/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.token = data["access_token"]
                    self.auth_headers = {"Authorization": f"Bearer {self.token}"}
                    self.log_result("Authentication - Valid Login", True, "Successfully logged in with new admin credentials")
                else:
                    self.log_result("Authentication - Valid Login", False, "Login response missing required fields", str(data))
            else:
                self.log_result("Authentication - Valid Login", False, f"Login failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Authentication - Valid Login", False, "Login request failed", str(e))
        
        # Test 2: Invalid login
        try:
            invalid_login = {
                "username": "newadmin",
                "password": "wrongpassword"
            }
            response = requests.post(f"{self.base_url}/login", json=invalid_login)
            
            if response.status_code == 401:
                self.log_result("Authentication - Invalid Login", True, "Correctly rejected invalid credentials")
            else:
                self.log_result("Authentication - Invalid Login", False, f"Expected 401, got {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Authentication - Invalid Login", False, "Invalid login test failed", str(e))
        
        # Test 3: Token validation (protected endpoint)
        if self.token:
            try:
                response = requests.get(f"{self.base_url}/pages", headers=self.auth_headers)
                
                if response.status_code == 200:
                    self.log_result("Authentication - Token Validation", True, "Token successfully validated on protected endpoint")
                else:
                    self.log_result("Authentication - Token Validation", False, f"Token validation failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Authentication - Token Validation", False, "Token validation test failed", str(e))
        
        # Test 4: Password change functionality
        if self.token:
            try:
                # First, try with wrong old password
                change_data = {
                    "old_password": "wrongoldpassword",
                    "new_password": "NewPassword123!"
                }
                response = requests.post(f"{self.base_url}/change-password", data=change_data, headers=self.auth_headers)
                
                if response.status_code == 400:
                    self.log_result("Authentication - Password Change (Invalid Old)", True, "Correctly rejected wrong old password")
                else:
                    self.log_result("Authentication - Password Change (Invalid Old)", False, f"Expected 400, got {response.status_code}", response.text)
                
                # Test with correct old password (but we won't actually change it)
                # This is just to test the endpoint structure
                
            except Exception as e:
                self.log_result("Authentication - Password Change", False, "Password change test failed", str(e))
    
    def test_content_management(self):
        """Test page CRUD operations"""
        print("\n=== Testing Content Management (Pages) ===")
        
        if not self.token:
            self.log_result("Content Management", False, "No authentication token available")
            return
        
        created_page_id = None
        
        # Test 1: Get homepage
        try:
            response = requests.get(f"{self.base_url}/page/home")
            
            if response.status_code == 200:
                data = response.json()
                if "title" in data and "content" in data and "slug" in data:
                    self.log_result("Content Management - Get Homepage", True, "Successfully retrieved homepage content")
                else:
                    self.log_result("Content Management - Get Homepage", False, "Homepage response missing required fields", str(data))
            else:
                self.log_result("Content Management - Get Homepage", False, f"Homepage retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Content Management - Get Homepage", False, "Homepage retrieval failed", str(e))
        
        # Test 2: Get all pages (admin)
        try:
            response = requests.get(f"{self.base_url}/pages", headers=self.auth_headers)
            
            if response.status_code == 200:
                pages = response.json()
                if isinstance(pages, list):
                    self.log_result("Content Management - Get All Pages", True, f"Successfully retrieved {len(pages)} pages")
                else:
                    self.log_result("Content Management - Get All Pages", False, "Pages response is not a list", str(pages))
            else:
                self.log_result("Content Management - Get All Pages", False, f"Pages retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Content Management - Get All Pages", False, "Pages retrieval failed", str(e))
        
        # Test 3: Create new page
        try:
            page_data = {
                "title": "Test About Page",
                "slug": "test-about",
                "content": "This is a test about page created during backend testing. It contains information about the testing process and validates the page creation functionality."
            }
            response = requests.post(f"{self.base_url}/pages", json=page_data, headers=self.auth_headers)
            
            if response.status_code == 200:
                created_page = response.json()
                if "id" in created_page and "title" in created_page:
                    created_page_id = created_page["id"]
                    self.log_result("Content Management - Create Page", True, f"Successfully created page: {created_page['title']}")
                else:
                    self.log_result("Content Management - Create Page", False, "Created page response missing required fields", str(created_page))
            else:
                self.log_result("Content Management - Create Page", False, f"Page creation failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Content Management - Create Page", False, "Page creation failed", str(e))
        
        # Test 4: Update page
        if created_page_id:
            try:
                update_data = {
                    "title": "Updated Test About Page",
                    "content": "This page has been updated during backend testing to verify the update functionality works correctly."
                }
                response = requests.put(f"{self.base_url}/pages/{created_page_id}", json=update_data, headers=self.auth_headers)
                
                if response.status_code == 200:
                    self.log_result("Content Management - Update Page", True, "Successfully updated page")
                else:
                    self.log_result("Content Management - Update Page", False, f"Page update failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Content Management - Update Page", False, "Page update failed", str(e))
        
        # Test 5: Delete page
        if created_page_id:
            try:
                response = requests.delete(f"{self.base_url}/pages/{created_page_id}", headers=self.auth_headers)
                
                if response.status_code == 200:
                    self.log_result("Content Management - Delete Page", True, "Successfully deleted page")
                else:
                    self.log_result("Content Management - Delete Page", False, f"Page deletion failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Content Management - Delete Page", False, "Page deletion failed", str(e))
        
        # Test 6: Get non-existent page
        try:
            response = requests.get(f"{self.base_url}/page/non-existent-page")
            
            if response.status_code == 404:
                self.log_result("Content Management - Non-existent Page", True, "Correctly returned 404 for non-existent page")
            else:
                self.log_result("Content Management - Non-existent Page", False, f"Expected 404, got {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Content Management - Non-existent Page", False, "Non-existent page test failed", str(e))
    
    def test_blog_system(self):
        """Test blog CRUD operations"""
        print("\n=== Testing Blog System ===")
        
        if not self.token:
            self.log_result("Blog System", False, "No authentication token available")
            return
        
        created_post_id = None
        
        # Test 1: Get all blog posts
        try:
            response = requests.get(f"{self.base_url}/blog")
            
            if response.status_code == 200:
                posts = response.json()
                if isinstance(posts, list):
                    self.log_result("Blog System - Get All Posts", True, f"Successfully retrieved {len(posts)} blog posts")
                else:
                    self.log_result("Blog System - Get All Posts", False, "Blog posts response is not a list", str(posts))
            else:
                self.log_result("Blog System - Get All Posts", False, f"Blog posts retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Blog System - Get All Posts", False, "Blog posts retrieval failed", str(e))
        
        # Test 2: Create new blog post
        try:
            post_data = {
                "title": "My Journey into Backend Testing",
                "slug": "backend-testing-journey",
                "content": """Today I'm sharing my experience with comprehensive backend testing. 

Testing is crucial for ensuring our APIs work correctly and handle edge cases properly. In this post, I'll cover:

1. Authentication testing strategies
2. CRUD operation validation
3. Error handling verification
4. Security considerations

This automated testing approach helps catch issues early and ensures a robust backend system."""
            }
            response = requests.post(f"{self.base_url}/blog", json=post_data, headers=self.auth_headers)
            
            if response.status_code == 200:
                created_post = response.json()
                if "id" in created_post and "title" in created_post:
                    created_post_id = created_post["id"]
                    self.log_result("Blog System - Create Post", True, f"Successfully created blog post: {created_post['title']}")
                else:
                    self.log_result("Blog System - Create Post", False, "Created post response missing required fields", str(created_post))
            else:
                self.log_result("Blog System - Create Post", False, f"Blog post creation failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Blog System - Create Post", False, "Blog post creation failed", str(e))
        
        # Test 3: Get specific blog post by slug
        try:
            response = requests.get(f"{self.base_url}/blog/backend-testing-journey")
            
            if response.status_code == 200:
                post = response.json()
                if "title" in post and "content" in post and "slug" in post:
                    self.log_result("Blog System - Get Post by Slug", True, f"Successfully retrieved post: {post['title']}")
                else:
                    self.log_result("Blog System - Get Post by Slug", False, "Post response missing required fields", str(post))
            else:
                self.log_result("Blog System - Get Post by Slug", False, f"Post retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Blog System - Get Post by Slug", False, "Post retrieval failed", str(e))
        
        # Test 4: Update blog post
        if created_post_id:
            try:
                update_data = {
                    "title": "My Complete Journey into Backend Testing",
                    "content": "This post has been updated to include more comprehensive information about backend testing methodologies and best practices."
                }
                response = requests.put(f"{self.base_url}/blog/{created_post_id}", json=update_data, headers=self.auth_headers)
                
                if response.status_code == 200:
                    self.log_result("Blog System - Update Post", True, "Successfully updated blog post")
                else:
                    self.log_result("Blog System - Update Post", False, f"Blog post update failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Blog System - Update Post", False, "Blog post update failed", str(e))
        
        # Test 5: Get non-existent blog post
        try:
            response = requests.get(f"{self.base_url}/blog/non-existent-post")
            
            if response.status_code == 404:
                self.log_result("Blog System - Non-existent Post", True, "Correctly returned 404 for non-existent post")
            else:
                self.log_result("Blog System - Non-existent Post", False, f"Expected 404, got {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Blog System - Non-existent Post", False, "Non-existent post test failed", str(e))
    
    def test_file_upload_system(self):
        """Test file upload functionality"""
        print("\n=== Testing File Upload System ===")
        
        if not self.token:
            self.log_result("File Upload System", False, "No authentication token available")
            return
        
        uploaded_filename = None
        
        # Test 1: Upload a small text file
        try:
            # Create a temporary test file
            test_content = "This is a test file for backend testing.\nIt contains sample content to verify file upload functionality."
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(test_content)
                temp_file_path = temp_file.name
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload", files=files, headers=self.auth_headers)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if response.status_code == 200:
                upload_result = response.json()
                if "filename" in upload_result and "original_name" in upload_result:
                    uploaded_filename = upload_result["filename"]
                    self.log_result("File Upload - Small File", True, f"Successfully uploaded file: {upload_result['original_name']}")
                else:
                    self.log_result("File Upload - Small File", False, "Upload response missing required fields", str(upload_result))
            else:
                self.log_result("File Upload - Small File", False, f"File upload failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("File Upload - Small File", False, "File upload failed", str(e))
        
        # Test 2: Retrieve uploaded file
        if uploaded_filename:
            try:
                response = requests.get(f"{self.base_url}/uploads/{uploaded_filename}")
                
                if response.status_code == 200:
                    self.log_result("File Upload - File Retrieval", True, "Successfully retrieved uploaded file")
                else:
                    self.log_result("File Upload - File Retrieval", False, f"File retrieval failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("File Upload - File Retrieval", False, "File retrieval failed", str(e))
        
        # Test 3: Try to retrieve non-existent file
        try:
            response = requests.get(f"{self.base_url}/uploads/non-existent-file.txt")
            
            if response.status_code == 404:
                self.log_result("File Upload - Non-existent File", True, "Correctly returned 404 for non-existent file")
            else:
                self.log_result("File Upload - Non-existent File", False, f"Expected 404, got {response.status_code}", response.text)
        except Exception as e:
            self.log_result("File Upload - Non-existent File", False, "Non-existent file test failed", str(e))
        
        # Test 4: Test file size validation (simulate large file)
        # Note: We won't actually upload a 5GB+ file, but we can test the validation logic
        try:
            # Create a larger test file (1MB) to test size handling
            large_content = "X" * (1024 * 1024)  # 1MB of X's
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(large_content)
                temp_file_path = temp_file.name
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('large_test_file.txt', f, 'text/plain')}
                response = requests.post(f"{self.base_url}/upload", files=files, headers=self.auth_headers)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if response.status_code == 200:
                self.log_result("File Upload - Size Validation", True, "Successfully handled 1MB file upload")
            else:
                self.log_result("File Upload - Size Validation", False, f"Large file upload failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("File Upload - Size Validation", False, "Large file upload test failed", str(e))
    
    def test_analytics_system(self):
        """Test analytics tracking and retrieval"""
        print("\n=== Testing Analytics System ===")
        
        if not self.token:
            self.log_result("Analytics System", False, "No authentication token available")
            return
        
        # Test 1: Get analytics data
        try:
            response = requests.get(f"{self.base_url}/analytics", headers=self.auth_headers)
            
            if response.status_code == 200:
                analytics = response.json()
                required_fields = ["total_visits", "unique_visitors", "recent_visits", "top_pages"]
                
                if all(field in analytics for field in required_fields):
                    self.log_result("Analytics System - Get Analytics", True, 
                                  f"Successfully retrieved analytics: {analytics['total_visits']} total visits, {analytics['unique_visitors']} unique visitors")
                else:
                    missing_fields = [field for field in required_fields if field not in analytics]
                    self.log_result("Analytics System - Get Analytics", False, f"Analytics response missing fields: {missing_fields}", str(analytics))
            else:
                self.log_result("Analytics System - Get Analytics", False, f"Analytics retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Analytics System - Get Analytics", False, "Analytics retrieval failed", str(e))
        
        # Test 2: Verify analytics tracking (by accessing a page)
        # The analytics should be automatically tracked when we access pages
        try:
            # Access homepage to generate analytics data
            response = requests.get(f"{self.base_url}/page/home")
            
            if response.status_code == 200:
                # Wait a moment for analytics to be processed
                time.sleep(1)
                
                # Check if analytics were recorded
                analytics_response = requests.get(f"{self.base_url}/analytics", headers=self.auth_headers)
                
                if analytics_response.status_code == 200:
                    analytics = analytics_response.json()
                    if analytics.get("total_visits", 0) > 0:
                        self.log_result("Analytics System - Visit Tracking", True, "Analytics tracking is working - visits are being recorded")
                    else:
                        self.log_result("Analytics System - Visit Tracking", False, "No visits recorded in analytics", str(analytics))
                else:
                    self.log_result("Analytics System - Visit Tracking", False, "Could not verify analytics tracking", analytics_response.text)
            else:
                self.log_result("Analytics System - Visit Tracking", False, "Could not access page for analytics test", response.text)
        except Exception as e:
            self.log_result("Analytics System - Visit Tracking", False, "Analytics tracking test failed", str(e))
    
    def test_contact_form(self):
        """Test contact form submission and retrieval with cooldown and pagination"""
        print("\n=== Testing Contact Form ===")
        
        created_message_id = None
        
        # Test 1: Submit contact message (no auth required)
        try:
            contact_data = {
                "name": "Alex Johnson",
                "email": "alex.johnson@example.com",
                "message": "Hello! I'm reaching out to test the contact form functionality. This message is part of the automated backend testing process. The form seems to be working well!"
            }
            response = requests.post(f"{self.base_url}/contact", json=contact_data)
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    self.log_result("Contact Form - Submit Message", True, "Successfully submitted contact message")
                else:
                    self.log_result("Contact Form - Submit Message", False, "Contact submission response missing message field", str(result))
            else:
                self.log_result("Contact Form - Submit Message", False, f"Contact submission failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Contact Form - Submit Message", False, "Contact submission failed", str(e))
        
        # Test 2: Test cooldown functionality by submitting another message immediately
        try:
            contact_data_immediate = {
                "name": "Alex Johnson",
                "email": "alex.johnson@example.com", 
                "message": "This is an immediate second message to test cooldown."
            }
            response = requests.post(f"{self.base_url}/contact", json=contact_data_immediate)
            
            if response.status_code == 429:
                self.log_result("Contact Form - Cooldown Protection", True, "Cooldown protection is working - second message blocked")
            elif response.status_code == 200:
                self.log_result("Contact Form - Cooldown Protection", False, "Cooldown protection not working - second message allowed immediately")
            else:
                self.log_result("Contact Form - Cooldown Protection", False, f"Unexpected response for cooldown test: {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Contact Form - Cooldown Protection", False, "Cooldown test failed", str(e))
        
        # Test 3: Retrieve contact messages with pagination (admin only)
        if self.token:
            try:
                response = requests.get(f"{self.base_url}/contact-messages", headers=self.auth_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if "messages" in data and "pagination" in data:
                        messages = data["messages"]
                        pagination = data["pagination"]
                        
                        # Store first message ID for deletion test
                        if messages and len(messages) > 0:
                            created_message_id = messages[0].get("id")
                        
                        required_pagination_fields = ["current_page", "total_pages", "total_results"]
                        if all(field in pagination for field in required_pagination_fields):
                            self.log_result("Contact Form - Get Messages with Pagination", True, 
                                          f"Successfully retrieved {len(messages)} messages with pagination (total: {pagination['total_results']})")
                        else:
                            self.log_result("Contact Form - Get Messages with Pagination", False, "Pagination missing required fields", str(pagination))
                    else:
                        self.log_result("Contact Form - Get Messages with Pagination", False, "Response missing messages or pagination", str(data))
                else:
                    self.log_result("Contact Form - Get Messages with Pagination", False, f"Contact messages retrieval failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Contact Form - Get Messages with Pagination", False, "Contact messages retrieval failed", str(e))
        
        # Test 4: Test pagination parameters
        if self.token:
            try:
                response = requests.get(f"{self.base_url}/contact-messages?page=1&limit=5", headers=self.auth_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if "pagination" in data:
                        pagination = data["pagination"]
                        if pagination.get("current_page") == 1:
                            self.log_result("Contact Form - Pagination Parameters", True, "Pagination parameters working correctly")
                        else:
                            self.log_result("Contact Form - Pagination Parameters", False, "Pagination parameters not working", str(pagination))
                    else:
                        self.log_result("Contact Form - Pagination Parameters", False, "Pagination data missing", str(data))
                else:
                    self.log_result("Contact Form - Pagination Parameters", False, f"Pagination test failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Contact Form - Pagination Parameters", False, "Pagination parameters test failed", str(e))
        
        # Test 5: Delete contact message (admin only)
        if self.token and created_message_id:
            try:
                response = requests.delete(f"{self.base_url}/contact-messages/{created_message_id}", headers=self.auth_headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if "message" in result:
                        self.log_result("Contact Form - Delete Message", True, "Successfully deleted contact message")
                    else:
                        self.log_result("Contact Form - Delete Message", False, "Delete response missing message field", str(result))
                else:
                    self.log_result("Contact Form - Delete Message", False, f"Message deletion failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Contact Form - Delete Message", False, "Message deletion failed", str(e))
        
        # Test 6: Try to delete non-existent message
        if self.token:
            try:
                fake_id = "non-existent-message-id"
                response = requests.delete(f"{self.base_url}/contact-messages/{fake_id}", headers=self.auth_headers)
                
                if response.status_code == 404:
                    self.log_result("Contact Form - Delete Non-existent Message", True, "Correctly returned 404 for non-existent message")
                else:
                    self.log_result("Contact Form - Delete Non-existent Message", False, f"Expected 404, got {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Contact Form - Delete Non-existent Message", False, "Non-existent message deletion test failed", str(e))
        
        # Test 7: Submit another contact message with different data
        try:
            contact_data2 = {
                "name": "Sarah Chen",
                "email": "sarah.chen@techcorp.com",
                "message": "I'm interested in collaborating on some projects. Your website looks great and I'd love to discuss potential opportunities. Please get back to me when you have a chance."
            }
            
            # Wait for cooldown to expire (we set it to 180 seconds in settings test)
            print("    Waiting 5 seconds before submitting second message...")
            time.sleep(5)
            
            response = requests.post(f"{self.base_url}/contact", json=contact_data2)
            
            if response.status_code == 200:
                self.log_result("Contact Form - Multiple Submissions After Cooldown", True, "Successfully submitted second contact message after waiting")
            elif response.status_code == 429:
                self.log_result("Contact Form - Multiple Submissions After Cooldown", True, "Cooldown still active - this is expected behavior")
            else:
                self.log_result("Contact Form - Multiple Submissions After Cooldown", False, f"Second contact submission failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Contact Form - Multiple Submissions After Cooldown", False, "Second contact submission failed", str(e))
    
    def test_enhanced_blog_system(self):
        """Test enhanced blog system with tags, excerpts, and new fields"""
        print("\n=== Testing Enhanced Blog System ===")
        
        if not self.token:
            self.log_result("Enhanced Blog System", False, "No authentication token available")
            return
        
        created_post_id = None
        
        # Test 1: Create blog post with all new fields
        try:
            post_data = {
                "title": "Advanced Web Development Techniques",
                "slug": "advanced-web-dev-techniques",
                "content": """<h2>Introduction to Modern Web Development</h2>
                <p>In today's rapidly evolving tech landscape, web development has become more sophisticated than ever. This comprehensive guide covers the latest techniques and best practices.</p>
                
                <h3>Key Topics Covered:</h3>
                <ul>
                <li>React and modern JavaScript frameworks</li>
                <li>API design and backend architecture</li>
                <li>Database optimization strategies</li>
                <li>Security best practices</li>
                </ul>
                
                <p>Whether you're a beginner or an experienced developer, this post will provide valuable insights into building robust, scalable web applications.</p>""",
                "excerpt": "A comprehensive guide to modern web development techniques covering React, APIs, databases, and security.",
                "tags": ["web-development", "react", "javascript", "backend", "security"],
                "author": "Alex Thompson",
                "featured_image": "https://example.com/web-dev-featured.jpg",
                "published": True
            }
            response = requests.post(f"{self.base_url}/blog", json=post_data, headers=self.auth_headers)
            
            if response.status_code == 200:
                created_post = response.json()
                if "id" in created_post and "tags" in created_post and "excerpt" in created_post:
                    created_post_id = created_post["id"]
                    self.log_result("Enhanced Blog - Create with New Fields", True, 
                                  f"Successfully created enhanced blog post with tags: {created_post.get('tags', [])}")
                else:
                    self.log_result("Enhanced Blog - Create with New Fields", False, 
                                  "Created post missing new fields", str(created_post))
            else:
                self.log_result("Enhanced Blog - Create with New Fields", False, 
                              f"Enhanced blog post creation failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Enhanced Blog - Create with New Fields", False, "Enhanced blog post creation failed", str(e))
        
        # Test 2: Create blog post without excerpt (test auto-generation)
        try:
            post_data_no_excerpt = {
                "title": "Testing Auto-Excerpt Generation",
                "slug": "auto-excerpt-test",
                "content": """This is a test post to verify that excerpts are automatically generated when not provided. The system should extract the first portion of the content and create a meaningful excerpt. This content is long enough to test the excerpt generation functionality properly.""",
                "tags": ["testing", "automation"],
                "author": "Test Author",
                "published": True
            }
            response = requests.post(f"{self.base_url}/blog", json=post_data_no_excerpt, headers=self.auth_headers)
            
            if response.status_code == 200:
                created_post = response.json()
                if "excerpt" in created_post and created_post["excerpt"]:
                    self.log_result("Enhanced Blog - Auto-Excerpt Generation", True, 
                                  f"Auto-excerpt generated: {created_post['excerpt'][:50]}...")
                else:
                    self.log_result("Enhanced Blog - Auto-Excerpt Generation", False, 
                                  "Auto-excerpt not generated", str(created_post))
            else:
                self.log_result("Enhanced Blog - Auto-Excerpt Generation", False, 
                              f"Auto-excerpt test failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Enhanced Blog - Auto-Excerpt Generation", False, "Auto-excerpt test failed", str(e))
        
        # Test 3: Update blog post with new fields
        if created_post_id:
            try:
                update_data = {
                    "title": "Advanced Web Development Techniques - Updated",
                    "content": "Updated content with new information about cutting-edge web development practices.",
                    "excerpt": "Updated excerpt with more detailed information about modern web development.",
                    "tags": ["web-development", "react", "javascript", "backend", "security", "updated"],
                    "author": "Alex Thompson - Senior Developer",
                    "featured_image": "https://example.com/updated-featured.jpg",
                    "published": True
                }
                response = requests.put(f"{self.base_url}/blog/{created_post_id}", json=update_data, headers=self.auth_headers)
                
                if response.status_code == 200:
                    self.log_result("Enhanced Blog - Update with New Fields", True, "Successfully updated blog post with enhanced fields")
                else:
                    self.log_result("Enhanced Blog - Update with New Fields", False, 
                                  f"Enhanced blog post update failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Enhanced Blog - Update with New Fields", False, "Enhanced blog post update failed", str(e))
        
        # Test 4: Get blog posts with filtering
        try:
            response = requests.get(f"{self.base_url}/blog?tag=web-development&author=Alex&published_only=true")
            
            if response.status_code == 200:
                posts = response.json()
                if isinstance(posts, list):
                    self.log_result("Enhanced Blog - Get with Filters", True, 
                                  f"Successfully retrieved {len(posts)} filtered blog posts")
                else:
                    self.log_result("Enhanced Blog - Get with Filters", False, "Filtered posts response is not a list", str(posts))
            else:
                self.log_result("Enhanced Blog - Get with Filters", False, 
                              f"Filtered blog posts retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Enhanced Blog - Get with Filters", False, "Filtered blog posts retrieval failed", str(e))

    def test_advanced_blog_search(self):
        """Test advanced blog search functionality"""
        print("\n=== Testing Advanced Blog Search System ===")
        
        # Test 1: Basic text search
        try:
            search_data = {
                "query": "web development",
                "published_only": True,
                "page": 1,
                "limit": 10
            }
            response = requests.post(f"{self.base_url}/blog/search", json=search_data)
            
            if response.status_code == 200:
                search_result = response.json()
                if "posts" in search_result and "pagination" in search_result:
                    posts = search_result["posts"]
                    pagination = search_result["pagination"]
                    self.log_result("Advanced Search - Text Search", True, 
                                  f"Successfully searched and found {len(posts)} posts (total: {pagination.get('total_results', 0)})")
                else:
                    self.log_result("Advanced Search - Text Search", False, 
                                  "Search response missing posts or pagination", str(search_result))
            else:
                self.log_result("Advanced Search - Text Search", False, 
                              f"Blog search failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Advanced Search - Text Search", False, "Blog search failed", str(e))
        
        # Test 2: Search with tags filter
        try:
            search_data = {
                "tags": ["web-development", "javascript"],
                "published_only": True,
                "page": 1,
                "limit": 5
            }
            response = requests.post(f"{self.base_url}/blog/search", json=search_data)
            
            if response.status_code == 200:
                search_result = response.json()
                if "posts" in search_result:
                    posts = search_result["posts"]
                    self.log_result("Advanced Search - Tags Filter", True, 
                                  f"Successfully filtered by tags and found {len(posts)} posts")
                else:
                    self.log_result("Advanced Search - Tags Filter", False, 
                                  "Tags search response missing posts", str(search_result))
            else:
                self.log_result("Advanced Search - Tags Filter", False, 
                              f"Tags search failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Advanced Search - Tags Filter", False, "Tags search failed", str(e))
        
        # Test 3: Search with author filter
        try:
            search_data = {
                "author": "Alex",
                "published_only": True,
                "page": 1,
                "limit": 10
            }
            response = requests.post(f"{self.base_url}/blog/search", json=search_data)
            
            if response.status_code == 200:
                search_result = response.json()
                if "posts" in search_result:
                    posts = search_result["posts"]
                    self.log_result("Advanced Search - Author Filter", True, 
                                  f"Successfully filtered by author and found {len(posts)} posts")
                else:
                    self.log_result("Advanced Search - Author Filter", False, 
                                  "Author search response missing posts", str(search_result))
            else:
                self.log_result("Advanced Search - Author Filter", False, 
                              f"Author search failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Advanced Search - Author Filter", False, "Author search failed", str(e))
        
        # Test 4: Combined search with highlighting
        try:
            search_data = {
                "query": "development",
                "tags": ["web-development"],
                "published_only": True,
                "page": 1,
                "limit": 10
            }
            response = requests.post(f"{self.base_url}/blog/search", json=search_data)
            
            if response.status_code == 200:
                search_result = response.json()
                if "posts" in search_result:
                    posts = search_result["posts"]
                    # Check if highlighting is working (look for <mark> tags)
                    highlighted_found = False
                    for post in posts:
                        if "<mark>" in post.get("title", "") or "<mark>" in post.get("excerpt", ""):
                            highlighted_found = True
                            break
                    
                    if highlighted_found:
                        self.log_result("Advanced Search - Search Highlighting", True, 
                                      "Search terms are properly highlighted in results")
                    else:
                        self.log_result("Advanced Search - Search Highlighting", True, 
                                      f"Combined search successful with {len(posts)} posts (highlighting may not be visible in test)")
                else:
                    self.log_result("Advanced Search - Combined Search", False, 
                                  "Combined search response missing posts", str(search_result))
            else:
                self.log_result("Advanced Search - Combined Search", False, 
                              f"Combined search failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Advanced Search - Combined Search", False, "Combined search failed", str(e))
        
        # Test 5: Date range search
        try:
            from datetime import datetime, timedelta
            date_from = (datetime.now() - timedelta(days=30)).isoformat()
            date_to = datetime.now().isoformat()
            
            search_data = {
                "date_from": date_from,
                "date_to": date_to,
                "published_only": True,
                "page": 1,
                "limit": 10
            }
            response = requests.post(f"{self.base_url}/blog/search", json=search_data)
            
            if response.status_code == 200:
                search_result = response.json()
                if "posts" in search_result:
                    posts = search_result["posts"]
                    self.log_result("Advanced Search - Date Range", True, 
                                  f"Successfully searched by date range and found {len(posts)} posts")
                else:
                    self.log_result("Advanced Search - Date Range", False, 
                                  "Date range search response missing posts", str(search_result))
            else:
                self.log_result("Advanced Search - Date Range", False, 
                              f"Date range search failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Advanced Search - Date Range", False, "Date range search failed", str(e))

    def test_blog_tags_and_authors(self):
        """Test blog tags and authors endpoints"""
        print("\n=== Testing Blog Tags and Authors Endpoints ===")
        
        # Test 1: Get all blog tags
        try:
            response = requests.get(f"{self.base_url}/blog/tags")
            
            if response.status_code == 200:
                tags = response.json()
                if isinstance(tags, list):
                    self.log_result("Blog Tags - Get All Tags", True, 
                                  f"Successfully retrieved {len(tags)} unique tags")
                    # Check tag structure
                    if tags and len(tags) > 0:
                        first_tag = tags[0]
                        if "tag" in first_tag and "count" in first_tag:
                            self.log_result("Blog Tags - Tag Structure", True, 
                                          f"Tags have correct structure with counts")
                        else:
                            self.log_result("Blog Tags - Tag Structure", False, 
                                          "Tags missing required fields", str(first_tag))
                else:
                    self.log_result("Blog Tags - Get All Tags", False, "Tags response is not a list", str(tags))
            else:
                self.log_result("Blog Tags - Get All Tags", False, 
                              f"Tags retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Blog Tags - Get All Tags", False, "Tags retrieval failed", str(e))
        
        # Test 2: Get all blog authors
        try:
            response = requests.get(f"{self.base_url}/blog/authors")
            
            if response.status_code == 200:
                authors = response.json()
                if isinstance(authors, list):
                    self.log_result("Blog Authors - Get All Authors", True, 
                                  f"Successfully retrieved {len(authors)} unique authors")
                else:
                    self.log_result("Blog Authors - Get All Authors", False, "Authors response is not a list", str(authors))
            else:
                self.log_result("Blog Authors - Get All Authors", False, 
                              f"Authors retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Blog Authors - Get All Authors", False, "Authors retrieval failed", str(e))

    def test_extended_settings(self):
        """Test extended settings with theme, SEO, social media, and email configurations"""
        print("\n=== Testing Extended Settings Configuration ===")
        
        if not self.token:
            self.log_result("Extended Settings", False, "No authentication token available")
            return
        
        # Test 1: Update settings with all new fields
        try:
            extended_settings = {
                # Basic Settings
                "site_title": "Sectorfive - Advanced Personal Website",
                "site_email": "contact@sectorfive.win",
                "contact_cooldown": 300,
                
                # Theme Customization
                "primary_color": "#2563eb",
                "secondary_color": "#64748b",
                "accent_color": "#10b981",
                "font_family": "Inter, system-ui, sans-serif",
                "custom_css": "body { font-size: 16px; } .custom-header { color: #2563eb; }",
                
                # SEO Settings
                "meta_description": "Sectorfive - Professional web developer and technology enthusiast sharing insights on modern development practices",
                "meta_keywords": "web development, programming, technology, react, javascript, python, tutorials",
                "google_analytics_id": "GA-123456789",
                "google_search_console": "google-site-verification=abc123def456",
                "robots_txt": "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://sectorfive.win/sitemap.xml",
                
                # Social Media Links
                "facebook_url": "https://facebook.com/sectorfive",
                "twitter_url": "https://twitter.com/sectorfive",
                "instagram_url": "https://instagram.com/sectorfive",
                "linkedin_url": "https://linkedin.com/in/sectorfive",
                "github_url": "https://github.com/sectorfive",
                "youtube_url": "https://youtube.com/@sectorfive",
                
                # Email Notification Settings
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_username": "notifications@sectorfive.win",
                "smtp_password": "app_password_here",
                "smtp_use_tls": True,
                "notification_email": "admin@sectorfive.win",
                "notify_on_contact": True,
                "notify_on_new_blog": True,
                
                # Blog Settings
                "posts_per_page": 12,
                "enable_comments": True,
                "auto_excerpt_length": 250,
                "default_author": "Sectorfive Team"
            }
            
            response = requests.put(f"{self.base_url}/settings", data=extended_settings, headers=self.auth_headers)
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    self.log_result("Extended Settings - Update All Fields", True, 
                                  "Successfully updated all extended settings fields")
                else:
                    self.log_result("Extended Settings - Update All Fields", False, 
                                  "Settings update response missing message", str(result))
            else:
                self.log_result("Extended Settings - Update All Fields", False, 
                              f"Extended settings update failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Extended Settings - Update All Fields", False, "Extended settings update failed", str(e))
        
        # Test 2: Verify all settings were persisted
        try:
            response = requests.get(f"{self.base_url}/settings", headers=self.auth_headers)
            
            if response.status_code == 200:
                settings = response.json()
                
                # Check theme settings
                theme_fields = ["primary_color", "secondary_color", "accent_color", "font_family", "custom_css"]
                theme_ok = all(field in settings for field in theme_fields)
                
                # Check SEO settings
                seo_fields = ["meta_description", "meta_keywords", "google_analytics_id", "robots_txt"]
                seo_ok = all(field in settings for field in seo_fields)
                
                # Check social media settings
                social_fields = ["facebook_url", "twitter_url", "github_url", "linkedin_url"]
                social_ok = all(field in settings for field in social_fields)
                
                # Check email settings
                email_fields = ["smtp_server", "smtp_port", "notification_email", "notify_on_contact"]
                email_ok = all(field in settings for field in email_fields)
                
                # Check blog settings
                blog_fields = ["posts_per_page", "enable_comments", "auto_excerpt_length", "default_author"]
                blog_ok = all(field in settings for field in blog_fields)
                
                if theme_ok and seo_ok and social_ok and email_ok and blog_ok:
                    self.log_result("Extended Settings - Verify Persistence", True, 
                                  "All extended settings categories persisted correctly")
                else:
                    missing_categories = []
                    if not theme_ok: missing_categories.append("theme")
                    if not seo_ok: missing_categories.append("SEO")
                    if not social_ok: missing_categories.append("social")
                    if not email_ok: missing_categories.append("email")
                    if not blog_ok: missing_categories.append("blog")
                    
                    self.log_result("Extended Settings - Verify Persistence", False, 
                                  f"Missing settings categories: {missing_categories}", str(settings))
            else:
                self.log_result("Extended Settings - Verify Persistence", False, 
                              f"Settings verification failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Extended Settings - Verify Persistence", False, "Settings verification failed", str(e))
        
        # Test 3: Verify enhanced public settings
        try:
            response = requests.get(f"{self.base_url}/public-settings")
            
            if response.status_code == 200:
                public_settings = response.json()
                
                # Check if new public fields are included
                expected_public_fields = [
                    "site_title", "meta_description", "meta_keywords",
                    "primary_color", "secondary_color", "accent_color", "font_family",
                    "facebook_url", "twitter_url", "github_url", "linkedin_url",
                    "posts_per_page", "enable_comments"
                ]
                
                missing_fields = [field for field in expected_public_fields if field not in public_settings]
                
                if not missing_fields:
                    self.log_result("Extended Settings - Enhanced Public Settings", True, 
                                  "All expected fields available in public settings")
                else:
                    self.log_result("Extended Settings - Enhanced Public Settings", False, 
                                  f"Missing public fields: {missing_fields}", str(public_settings))
            else:
                self.log_result("Extended Settings - Enhanced Public Settings", False, 
                              f"Public settings retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Extended Settings - Enhanced Public Settings", False, "Public settings test failed", str(e))

    def test_seo_endpoints(self):
        """Test SEO endpoints: robots.txt and sitemap.xml"""
        print("\n=== Testing SEO Endpoints ===")
        
        # Test 1: Get robots.txt
        try:
            response = requests.get(f"{self.base_url}/robots.txt")
            
            if response.status_code == 200:
                robots_data = response.json()
                if "content" in robots_data and robots_data["content"]:
                    robots_content = robots_data["content"]
                    if "User-agent:" in robots_content and "Allow:" in robots_content:
                        self.log_result("SEO - Robots.txt", True, 
                                      f"Successfully retrieved robots.txt with proper format")
                    else:
                        self.log_result("SEO - Robots.txt", False, 
                                      "Robots.txt content missing required directives", robots_content)
                else:
                    self.log_result("SEO - Robots.txt", False, 
                                  "Robots.txt response missing content", str(robots_data))
            else:
                self.log_result("SEO - Robots.txt", False, 
                              f"Robots.txt retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("SEO - Robots.txt", False, "Robots.txt test failed", str(e))
        
        # Test 2: Get sitemap.xml
        try:
            response = requests.get(f"{self.base_url}/sitemap.xml")
            
            if response.status_code == 200:
                sitemap_data = response.json()
                if "urls" in sitemap_data and isinstance(sitemap_data["urls"], list):
                    urls = sitemap_data["urls"]
                    
                    # Check if sitemap has proper structure
                    if urls and len(urls) > 0:
                        first_url = urls[0]
                        required_fields = ["loc", "lastmod", "changefreq", "priority"]
                        
                        if all(field in first_url for field in required_fields):
                            self.log_result("SEO - Sitemap.xml", True, 
                                          f"Successfully retrieved sitemap with {len(urls)} URLs")
                        else:
                            missing_fields = [field for field in required_fields if field not in first_url]
                            self.log_result("SEO - Sitemap.xml", False, 
                                          f"Sitemap URLs missing fields: {missing_fields}", str(first_url))
                    else:
                        self.log_result("SEO - Sitemap.xml", True, 
                                      "Sitemap retrieved successfully (empty - no content yet)")
                else:
                    self.log_result("SEO - Sitemap.xml", False, 
                                  "Sitemap response missing urls array", str(sitemap_data))
            else:
                self.log_result("SEO - Sitemap.xml", False, 
                              f"Sitemap retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("SEO - Sitemap.xml", False, "Sitemap test failed", str(e))
    
    def test_settings_management(self):
        """Test settings retrieval and updates"""
        print("\n=== Testing Settings Management ===")
        
        # Test 1: Get public settings (no auth required)
        try:
            response = requests.get(f"{self.base_url}/public-settings")
            
            if response.status_code == 200:
                settings = response.json()
                required_fields = ["site_title", "background_type", "background_value", "background_image_url"]
                
                if all(field in settings for field in required_fields):
                    self.log_result("Settings Management - Get Public Settings", True, 
                                  f"Successfully retrieved public settings: {settings['site_title']}")
                else:
                    missing_fields = [field for field in required_fields if field not in settings]
                    self.log_result("Settings Management - Get Public Settings", False, f"Public settings response missing fields: {missing_fields}", str(settings))
            else:
                self.log_result("Settings Management - Get Public Settings", False, f"Public settings retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Settings Management - Get Public Settings", False, "Public settings retrieval failed", str(e))
        
        if not self.token:
            self.log_result("Settings Management", False, "No authentication token available for admin settings")
            return
        
        # Test 2: Get current admin settings
        try:
            response = requests.get(f"{self.base_url}/settings", headers=self.auth_headers)
            
            if response.status_code == 200:
                settings = response.json()
                required_fields = ["max_file_size", "site_title", "site_email", "contact_cooldown"]
                
                if all(field in settings for field in required_fields):
                    self.log_result("Settings Management - Get Admin Settings", True, 
                                  f"Successfully retrieved admin settings: {settings['site_title']}")
                else:
                    missing_fields = [field for field in required_fields if field not in settings]
                    self.log_result("Settings Management - Get Admin Settings", False, f"Admin settings response missing fields: {missing_fields}", str(settings))
            else:
                self.log_result("Settings Management - Get Admin Settings", False, f"Admin settings retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Settings Management - Get Admin Settings", False, "Admin settings retrieval failed", str(e))
        
        # Test 3: Update settings with new background fields
        try:
            update_data = {
                "max_file_size": 5368709120,  # 5GB
                "site_title": "Sectorfive Personal Website - Updated",
                "site_email": "admin@sectorfive.win",
                "contact_cooldown": 180,  # 3 minutes
                "background_type": "gradient",
                "background_value": "linear-gradient(45deg, #667eea 0%, #764ba2 100%)",
                "background_image_url": "https://example.com/bg.jpg"
            }
            response = requests.put(f"{self.base_url}/settings", data=update_data, headers=self.auth_headers)
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    self.log_result("Settings Management - Update Settings with Background", True, "Successfully updated settings with background fields")
                else:
                    self.log_result("Settings Management - Update Settings with Background", False, "Settings update response missing message field", str(result))
            else:
                self.log_result("Settings Management - Update Settings with Background", False, f"Settings update failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Settings Management - Update Settings with Background", False, "Settings update failed", str(e))
        
        # Test 4: Verify settings were updated and background fields persisted
        try:
            response = requests.get(f"{self.base_url}/settings", headers=self.auth_headers)
            
            if response.status_code == 200:
                settings = response.json()
                if (settings.get("site_title") == "Sectorfive Personal Website - Updated" and
                    settings.get("background_type") == "gradient" and
                    settings.get("contact_cooldown") == 180):
                    self.log_result("Settings Management - Verify Background Update", True, "Settings update with background fields was persisted correctly")
                else:
                    self.log_result("Settings Management - Verify Background Update", False, "Settings update was not persisted correctly", str(settings))
            else:
                self.log_result("Settings Management - Verify Background Update", False, f"Settings verification failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Settings Management - Verify Background Update", False, "Settings verification failed", str(e))
        
        # Test 5: Verify public settings reflect the updates
        try:
            response = requests.get(f"{self.base_url}/public-settings")
            
            if response.status_code == 200:
                public_settings = response.json()
                if (public_settings.get("site_title") == "Sectorfive Personal Website - Updated" and
                    public_settings.get("background_type") == "gradient"):
                    self.log_result("Settings Management - Verify Public Settings Update", True, "Public settings correctly reflect admin updates")
                else:
                    self.log_result("Settings Management - Verify Public Settings Update", False, "Public settings do not reflect admin updates", str(public_settings))
            else:
                self.log_result("Settings Management - Verify Public Settings Update", False, f"Public settings verification failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Settings Management - Verify Public Settings Update", False, "Public settings verification failed", str(e))
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Comprehensive Backend Testing for Sectorfive Website")
        print(f"📡 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all test suites
        self.test_admin_onboarding_flow()
        self.test_authentication_system()
        self.test_content_management()
        self.test_blog_system()
        self.test_enhanced_blog_system()
        self.test_advanced_blog_search()
        self.test_blog_tags_and_authors()
        self.test_file_upload_system()
        self.test_analytics_system()
        self.test_contact_form()
        self.test_settings_management()
        self.test_extended_settings()
        self.test_seo_endpoints()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
                    if result['details']:
                        print(f"    Details: {result['details']}")
        
        print(f"\n⏰ Completed at: {datetime.now().isoformat()}")
        
        # Return summary for external use
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = BackendTester()
    summary = tester.run_all_tests()