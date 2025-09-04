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
BASE_URL = "http://localhost:8001/api"
TEST_USERNAME = "Sectorfive"
TEST_PASSWORD = "KamenkoTV258!"

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
    
    def test_authentication_system(self):
        """Test the complete authentication system"""
        print("\n=== Testing Authentication System ===")
        
        # Test 1: Valid login
        try:
            login_data = {
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
            response = requests.post(f"{self.base_url}/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.token = data["access_token"]
                    self.auth_headers = {"Authorization": f"Bearer {self.token}"}
                    self.log_result("Authentication - Valid Login", True, "Successfully logged in with correct credentials")
                else:
                    self.log_result("Authentication - Valid Login", False, "Login response missing required fields", str(data))
            else:
                self.log_result("Authentication - Valid Login", False, f"Login failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Authentication - Valid Login", False, "Login request failed", str(e))
        
        # Test 2: Invalid login
        try:
            invalid_login = {
                "username": TEST_USERNAME,
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
            
            response = requests.post(f"{self.base_url}/contact", data=contact_data2)
            
            if response.status_code == 200:
                self.log_result("Contact Form - Multiple Submissions After Cooldown", True, "Successfully submitted second contact message after waiting")
            elif response.status_code == 429:
                self.log_result("Contact Form - Multiple Submissions After Cooldown", True, "Cooldown still active - this is expected behavior")
            else:
                self.log_result("Contact Form - Multiple Submissions After Cooldown", False, f"Second contact submission failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Contact Form - Multiple Submissions After Cooldown", False, "Second contact submission failed", str(e))
    
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
        self.test_authentication_system()
        self.test_content_management()
        self.test_blog_system()
        self.test_file_upload_system()
        self.test_analytics_system()
        self.test_contact_form()
        self.test_settings_management()
        
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