#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite for Personal Website
Focus: Gallery System, Port Configuration, Regression Testing, Security
"""

import requests
import json
import os
import tempfile
import time
from io import BytesIO
from PIL import Image
import uuid

# Configuration
BASE_URL = "https://retrodevkit.preview.emergentagent.com/api"
INTERNAL_URL = "http://localhost:8001/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            # Test with default admin credentials
            response = self.session.post(f"{BASE_URL}/login", json={
                "username": "admin",
                "password": "admin"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Admin Authentication", True, "Successfully authenticated with admin/admin")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Failed to authenticate: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_port_configuration(self):
        """Test port configuration and accessibility"""
        print("\n=== PORT CONFIGURATION TESTING ===")
        
        # Test internal port access
        try:
            response = requests.get(f"{INTERNAL_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Internal Port 8001 Access", True, "Backend accessible on internal port 8001")
            else:
                self.log_test("Internal Port 8001 Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Internal Port 8001 Access", False, f"Exception: {str(e)}")
        
        # Test external URL access
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("External URL Access", True, "Backend accessible via external URL")
            else:
                self.log_test("External URL Access", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("External URL Access", False, f"Exception: {str(e)}")
        
        # Test CORS configuration
        try:
            response = requests.options(f"{BASE_URL}/health", headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            })
            cors_headers = response.headers.get("Access-Control-Allow-Origin", "")
            if cors_headers == "*" or "localhost" in cors_headers:
                self.log_test("CORS Configuration", True, f"CORS properly configured: {cors_headers}")
            else:
                self.log_test("CORS Configuration", False, f"CORS headers: {cors_headers}")
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")
    
    def create_test_image(self, width=100, height=100, format='PNG'):
        """Create a test image file"""
        img = Image.new('RGB', (width, height), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes
    
    def test_gallery_system(self):
        """Test complete gallery system functionality"""
        print("\n=== GALLERY SYSTEM TESTING (HIGH PRIORITY) ===")
        
        if not self.token:
            self.log_test("Gallery System Setup", False, "No authentication token available")
            return
        
        # Test 1: Upload new image with metadata
        try:
            test_image = self.create_test_image()
            files = {
                'file': ('test_image.png', test_image, 'image/png')
            }
            data = {
                'title': 'Test Gallery Image',
                'description': 'A test image for gallery functionality',
                'tags': 'test,gallery,automation',
                'is_featured': 'true'
            }
            
            response = self.session.post(f"{BASE_URL}/gallery", files=files, data=data)
            
            if response.status_code == 200:
                gallery_data = response.json()
                self.test_image_id = gallery_data.get('id')
                self.log_test("Gallery Image Upload", True, f"Image uploaded with ID: {self.test_image_id}")
            else:
                self.log_test("Gallery Image Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                return
                
        except Exception as e:
            self.log_test("Gallery Image Upload", False, f"Exception: {str(e)}")
            return
        
        # Test 2: Retrieve gallery images with pagination
        try:
            response = self.session.get(f"{BASE_URL}/gallery?page=1&limit=10")
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                pagination = data.get('pagination', {})
                self.log_test("Gallery Retrieval", True, f"Retrieved {len(images)} images with pagination")
            else:
                self.log_test("Gallery Retrieval", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Gallery Retrieval", False, f"Exception: {str(e)}")
        
        # Test 3: Search gallery images
        try:
            response = self.session.get(f"{BASE_URL}/gallery?search=test")
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                self.log_test("Gallery Search", True, f"Search returned {len(images)} images")
            else:
                self.log_test("Gallery Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Gallery Search", False, f"Exception: {str(e)}")
        
        # Test 4: Filter by tags
        try:
            response = self.session.get(f"{BASE_URL}/gallery?tags=test")
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                self.log_test("Gallery Tag Filter", True, f"Tag filter returned {len(images)} images")
            else:
                self.log_test("Gallery Tag Filter", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Gallery Tag Filter", False, f"Exception: {str(e)}")
        
        # Test 5: Get specific gallery image
        if hasattr(self, 'test_image_id'):
            try:
                response = self.session.get(f"{BASE_URL}/gallery/{self.test_image_id}")
                if response.status_code == 200:
                    image_data = response.json()
                    self.log_test("Gallery Image Retrieval", True, f"Retrieved image: {image_data.get('title')}")
                else:
                    self.log_test("Gallery Image Retrieval", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Gallery Image Retrieval", False, f"Exception: {str(e)}")
        
        # Test 6: Update gallery image metadata
        if hasattr(self, 'test_image_id'):
            try:
                update_data = {
                    'title': 'Updated Test Image',
                    'description': 'Updated description',
                    'tags': ['updated', 'test'],
                    'is_featured': False
                }
                response = self.session.put(f"{BASE_URL}/gallery/{self.test_image_id}", json=update_data)
                if response.status_code == 200:
                    self.log_test("Gallery Image Update", True, "Image metadata updated successfully")
                else:
                    self.log_test("Gallery Image Update", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Gallery Image Update", False, f"Exception: {str(e)}")
        
        # Test 7: Get gallery tags
        try:
            response = self.session.get(f"{BASE_URL}/gallery/tags")
            if response.status_code == 200:
                tags = response.json()
                self.log_test("Gallery Tags Retrieval", True, f"Retrieved {len(tags)} unique tags")
            else:
                self.log_test("Gallery Tags Retrieval", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Gallery Tags Retrieval", False, f"Exception: {str(e)}")
        
        # Test 8: Delete gallery image
        if hasattr(self, 'test_image_id'):
            try:
                response = self.session.delete(f"{BASE_URL}/gallery/{self.test_image_id}")
                if response.status_code == 200:
                    self.log_test("Gallery Image Deletion", True, "Image deleted successfully")
                else:
                    self.log_test("Gallery Image Deletion", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Gallery Image Deletion", False, f"Exception: {str(e)}")
    
    def test_gallery_security(self):
        """Test gallery security and error handling"""
        print("\n=== GALLERY SECURITY & ERROR HANDLING ===")
        
        if not self.token:
            self.log_test("Gallery Security Setup", False, "No authentication token available")
            return
        
        # Test 1: Upload non-image file (should be rejected)
        try:
            files = {
                'file': ('test.txt', BytesIO(b'This is not an image'), 'text/plain')
            }
            data = {
                'title': 'Malicious File',
                'description': 'This should be rejected',
                'tags': 'malicious',
                'is_featured': 'false'
            }
            
            response = self.session.post(f"{BASE_URL}/gallery", files=files, data=data)
            
            if response.status_code == 400:
                self.log_test("Non-Image File Rejection", True, "Non-image files properly rejected")
            else:
                self.log_test("Non-Image File Rejection", False, f"Status: {response.status_code} - Should reject non-images")
                
        except Exception as e:
            self.log_test("Non-Image File Rejection", False, f"Exception: {str(e)}")
        
        # Test 2: Upload without authentication
        try:
            # Temporarily remove auth header
            auth_header = self.session.headers.pop('Authorization', None)
            
            test_image = self.create_test_image()
            files = {
                'file': ('test_image.png', test_image, 'image/png')
            }
            data = {
                'title': 'Unauthorized Upload',
                'description': 'This should be rejected',
                'tags': 'unauthorized',
                'is_featured': 'false'
            }
            
            response = self.session.post(f"{BASE_URL}/gallery", files=files, data=data)
            
            # Restore auth header
            if auth_header:
                self.session.headers['Authorization'] = auth_header
            
            if response.status_code == 401 or response.status_code == 403:
                self.log_test("Unauthorized Upload Rejection", True, "Unauthorized uploads properly rejected")
            else:
                self.log_test("Unauthorized Upload Rejection", False, f"Status: {response.status_code} - Should require authentication")
                
        except Exception as e:
            self.log_test("Unauthorized Upload Rejection", False, f"Exception: {str(e)}")
        
        # Test 3: Large file upload (test file size limits)
        try:
            # Create a large test image (simulate large file)
            large_image = self.create_test_image(2000, 2000)  # Larger image
            files = {
                'file': ('large_image.png', large_image, 'image/png')
            }
            data = {
                'title': 'Large Image Test',
                'description': 'Testing file size limits',
                'tags': 'large,test',
                'is_featured': 'false'
            }
            
            response = self.session.post(f"{BASE_URL}/gallery", files=files, data=data)
            
            if response.status_code in [200, 413]:  # Either success or file too large
                if response.status_code == 200:
                    # Clean up if successful
                    data = response.json()
                    image_id = data.get('id')
                    if image_id:
                        self.session.delete(f"{BASE_URL}/gallery/{image_id}")
                    self.log_test("Large File Handling", True, "Large file handled appropriately")
                else:
                    self.log_test("Large File Handling", True, "Large file properly rejected with 413")
            else:
                self.log_test("Large File Handling", False, f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Large File Handling", False, f"Exception: {str(e)}")
    
    def test_regression_functionality(self):
        """Test existing functionality to ensure no regressions"""
        print("\n=== REGRESSION TESTING ===")
        
        # Test 1: Authentication system
        try:
            response = self.session.get(f"{BASE_URL}/me")
            if response.status_code == 200:
                user_data = response.json()
                self.log_test("Authentication System", True, f"User: {user_data.get('username')}")
            else:
                self.log_test("Authentication System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Authentication System", False, f"Exception: {str(e)}")
        
        # Test 2: Blog system
        try:
            response = self.session.get(f"{BASE_URL}/blog")
            if response.status_code == 200:
                posts = response.json()
                self.log_test("Blog System", True, f"Retrieved {len(posts)} blog posts")
            else:
                self.log_test("Blog System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Blog System", False, f"Exception: {str(e)}")
        
        # Test 3: Pages system
        try:
            response = self.session.get(f"{BASE_URL}/pages")
            if response.status_code == 200:
                pages = response.json()
                self.log_test("Pages System", True, f"Retrieved {len(pages)} pages")
            else:
                self.log_test("Pages System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Pages System", False, f"Exception: {str(e)}")
        
        # Test 4: Settings system
        try:
            response = self.session.get(f"{BASE_URL}/settings")
            if response.status_code == 200:
                settings = response.json()
                self.log_test("Settings System", True, f"Settings retrieved with site_title: {settings.get('site_title')}")
            else:
                self.log_test("Settings System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Settings System", False, f"Exception: {str(e)}")
        
        # Test 5: Public settings (no auth required)
        try:
            # Temporarily remove auth header
            auth_header = self.session.headers.pop('Authorization', None)
            
            response = self.session.get(f"{BASE_URL}/public-settings")
            
            # Restore auth header
            if auth_header:
                self.session.headers['Authorization'] = auth_header
            
            if response.status_code == 200:
                settings = response.json()
                self.log_test("Public Settings", True, f"Public settings accessible without auth")
            else:
                self.log_test("Public Settings", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Public Settings", False, f"Exception: {str(e)}")
        
        # Test 6: Analytics system
        try:
            response = self.session.get(f"{BASE_URL}/analytics")
            if response.status_code == 200:
                analytics = response.json()
                self.log_test("Analytics System", True, f"Analytics: {analytics.get('total_visits', 0)} visits")
            else:
                self.log_test("Analytics System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Analytics System", False, f"Exception: {str(e)}")
        
        # Test 7: Contact form system
        try:
            response = self.session.get(f"{BASE_URL}/contact-messages")
            if response.status_code == 200:
                messages = response.json()
                total_messages = messages.get('pagination', {}).get('total_results', 0)
                self.log_test("Contact System", True, f"Contact messages: {total_messages} total")
            else:
                self.log_test("Contact System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Contact System", False, f"Exception: {str(e)}")
        
        # Test 8: File upload system
        try:
            test_file = BytesIO(b'Test file content')
            files = {'file': ('test.txt', test_file, 'text/plain')}
            
            response = self.session.post(f"{BASE_URL}/upload", files=files)
            if response.status_code == 200:
                file_data = response.json()
                filename = file_data.get('filename')
                self.log_test("File Upload System", True, f"File uploaded: {filename}")
                
                # Test file retrieval
                if filename:
                    file_response = self.session.get(f"{BASE_URL}/uploads/{filename}")
                    if file_response.status_code == 200:
                        self.log_test("File Retrieval System", True, "File retrieved successfully")
                    else:
                        self.log_test("File Retrieval System", False, f"Status: {file_response.status_code}")
            else:
                self.log_test("File Upload System", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("File Upload System", False, f"Exception: {str(e)}")
    
    def test_advanced_blog_features(self):
        """Test advanced blog search and enhanced features"""
        print("\n=== ADVANCED BLOG FEATURES TESTING ===")
        
        # Test 1: Blog search functionality
        try:
            search_data = {
                "query": "test",
                "page": 1,
                "limit": 10,
                "published_only": True
            }
            response = self.session.post(f"{BASE_URL}/blog/search", json=search_data)
            if response.status_code == 200:
                results = response.json()
                posts = results.get('posts', [])
                pagination = results.get('pagination', {})
                self.log_test("Blog Search", True, f"Search returned {len(posts)} posts")
            else:
                self.log_test("Blog Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Blog Search", False, f"Exception: {str(e)}")
        
        # Test 2: Blog tags endpoint
        try:
            response = self.session.get(f"{BASE_URL}/blog/tags")
            if response.status_code == 200:
                tags = response.json()
                self.log_test("Blog Tags", True, f"Retrieved {len(tags)} blog tags")
            else:
                self.log_test("Blog Tags", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Blog Tags", False, f"Exception: {str(e)}")
        
        # Test 3: Blog authors endpoint
        try:
            response = self.session.get(f"{BASE_URL}/blog/authors")
            if response.status_code == 200:
                authors = response.json()
                self.log_test("Blog Authors", True, f"Retrieved {len(authors)} blog authors")
            else:
                self.log_test("Blog Authors", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Blog Authors", False, f"Exception: {str(e)}")
    
    def test_seo_endpoints(self):
        """Test SEO-related endpoints"""
        print("\n=== SEO ENDPOINTS TESTING ===")
        
        # Test 1: Robots.txt endpoint
        try:
            response = self.session.get(f"{BASE_URL}/robots.txt")
            if response.status_code == 200:
                robots_data = response.json()
                content = robots_data.get('content', '')
                self.log_test("Robots.txt Endpoint", True, f"Robots.txt served with {len(content)} characters")
            else:
                self.log_test("Robots.txt Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Robots.txt Endpoint", False, f"Exception: {str(e)}")
        
        # Test 2: Sitemap.xml endpoint
        try:
            response = self.session.get(f"{BASE_URL}/sitemap.xml")
            if response.status_code == 200:
                sitemap_data = response.json()
                urls = sitemap_data.get('urls', [])
                self.log_test("Sitemap.xml Endpoint", True, f"Sitemap generated with {len(urls)} URLs")
            else:
                self.log_test("Sitemap.xml Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Sitemap.xml Endpoint", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Backend Testing Suite")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Run all test suites
        self.test_port_configuration()
        self.test_gallery_system()
        self.test_gallery_security()
        self.test_regression_functionality()
        self.test_advanced_blog_features()
        self.test_seo_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        return self.passed_tests, self.total_tests

if __name__ == "__main__":
    tester = BackendTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        exit(0)
    else:
        exit(1)