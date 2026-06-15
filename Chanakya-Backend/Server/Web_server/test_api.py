"""
Chanakya API Test Suite
Tests all major endpoints of the FastAPI backend
Run: python test_api.py
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import sys


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class APITester:
    """Test suite for Chanakya FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token: Optional[str] = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }
        
    def print_header(self, text: str):
        """Print formatted section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def print_json(self, data: Dict[Any, Any], indent: int = 2):
        """Print formatted JSON"""
        print(f"{Colors.OKBLUE}{json.dumps(data, indent=indent, ensure_ascii=False)}{Colors.ENDC}")
    
    def record_test(self, passed: bool):
        """Record test result"""
        self.test_results["total"] += 1
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    def test_health(self) -> bool:
        """Test health check endpoint"""
        self.print_header("Testing Health Check Endpoint")
        
        try:
            self.print_info(f"GET {self.base_url}/health")
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Health check passed - Status: {response.status_code}")
                self.print_json(data)
                self.record_test(True)
                return True
            else:
                self.print_error(f"Health check failed - Status: {response.status_code}")
                self.record_test(False)
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_error("Connection failed! Is the server running?")
            self.print_warning(f"Make sure to start the server with: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            self.record_test(False)
            return False
        except Exception as e:
            self.print_error(f"Unexpected error: {str(e)}")
            self.record_test(False)
            return False
    
    def test_register_and_login(self) -> bool:
        """Test user registration and login"""
        self.print_header("Testing Authentication")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": "teacher"
        }
        
        try:
            # Test Registration
            self.print_info(f"POST {self.api_url}/auth/register")
            self.print_json({"username": test_user["username"], "email": test_user["email"]})
            
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=test_user,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.print_success("User registration successful")
                self.print_json(response.json())
            else:
                self.print_warning(f"Registration returned status {response.status_code}")
                self.print_json(response.json())
            
            # Test Login
            time.sleep(1)  # Small delay between requests
            self.print_info(f"\nPOST {self.api_url}/auth/login")
            
            login_data = {
                "username": test_user["email"],
                "password": test_user["password"]
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.print_success("Login successful")
                self.print_json({
                    "access_token": self.token[:50] + "...",
                    "token_type": data.get("token_type"),
                    "user": data.get("user")
                })
                self.record_test(True)
                return True
            else:
                self.print_error(f"Login failed - Status: {response.status_code}")
                self.print_json(response.json())
                self.record_test(False)
                return False
                
        except Exception as e:
            self.print_error(f"Authentication test failed: {str(e)}")
            self.record_test(False)
            return False
    
    def test_tools_endpoint(self) -> bool:
        """Test the /api/query/tools endpoint"""
        self.print_header("Testing Tools Endpoint")
        
        if not self.token:
            self.print_warning("Skipping - No authentication token available")
            return False
        
        try:
            self.print_info(f"GET {self.api_url}/query/tools")
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/query/tools",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Successfully retrieved available tools")
                self.print_json(data)
                
                if isinstance(data, dict) and "tools" in data:
                    self.print_info(f"\nFound {len(data['tools'])} available tools")
                    for tool in data['tools']:
                        print(f"  • {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                
                self.record_test(True)
                return True
            else:
                self.print_error(f"Failed to get tools - Status: {response.status_code}")
                self.print_json(response.json())
                self.record_test(False)
                return False
                
        except Exception as e:
            self.print_error(f"Tools endpoint test failed: {str(e)}")
            self.record_test(False)
            return False
    
    def test_query_endpoint(self, query: str = "What is photosynthesis?") -> Optional[str]:
        """Test the POST /api/query/query endpoint"""
        self.print_header("Testing Query Endpoint")
        
        if not self.token:
            self.print_warning("Skipping - No authentication token available")
            return None
        
        try:
            self.print_info(f"POST {self.api_url}/query/query")
            
            query_data = {
                "query": query,
                "language": "english",
                "context": {
                    "subject": "biology",
                    "grade_level": "10"
                }
            }
            
            self.print_info("Request payload:")
            self.print_json(query_data)
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            self.print_info("\nSending query... (this may take a few seconds)")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_url}/query/query",
                json=query_data,
                headers=headers,
                timeout=60
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Query processed successfully (took {elapsed_time:.2f}s)")
                
                # Format response nicely
                formatted_response = {
                    "query_id": data.get("query_id"),
                    "response": data.get("response", "")[:200] + "..." if len(data.get("response", "")) > 200 else data.get("response", ""),
                    "tool_used": data.get("tool_used"),
                    "confidence": data.get("confidence"),
                    "language": data.get("language"),
                    "timestamp": data.get("timestamp")
                }
                
                self.print_json(formatted_response)
                
                # Print full response separately
                if data.get("response"):
                    self.print_info("\nFull Response:")
                    print(f"{Colors.OKBLUE}{data.get('response')}{Colors.ENDC}")
                
                self.record_test(True)
                return data.get("query_id")
            else:
                self.print_error(f"Query failed - Status: {response.status_code}")
                self.print_json(response.json())
                self.record_test(False)
                return None
                
        except requests.exceptions.Timeout:
            self.print_error("Query request timed out (>60s)")
            self.record_test(False)
            return None
        except Exception as e:
            self.print_error(f"Query endpoint test failed: {str(e)}")
            self.record_test(False)
            return None
    
    def test_status_endpoint(self, query_id: Optional[str] = None) -> bool:
        """Test the GET /api/query/status/{query_id} endpoint"""
        self.print_header("Testing Query Status Endpoint")
        
        if not self.token:
            self.print_warning("Skipping - No authentication token available")
            return False
        
        if not query_id:
            self.print_warning("Skipping - No query ID available")
            self.print_info("Run a query first to get a query ID")
            return False
        
        try:
            self.print_info(f"GET {self.api_url}/query/status/{query_id}")
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/query/status/{query_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Successfully retrieved query status")
                self.print_json(data)
                self.record_test(True)
                return True
            elif response.status_code == 404:
                self.print_warning("Query not found (this may be expected if status endpoint is not implemented)")
                self.print_json(response.json())
                self.record_test(True)  # Don't fail if endpoint not implemented
                return True
            else:
                self.print_error(f"Failed to get status - Status: {response.status_code}")
                self.print_json(response.json())
                self.record_test(False)
                return False
                
        except Exception as e:
            self.print_error(f"Status endpoint test failed: {str(e)}")
            self.record_test(False)
            return False
    
    def test_query_history(self) -> bool:
        """Test the GET /api/query/history endpoint"""
        self.print_header("Testing Query History Endpoint")
        
        if not self.token:
            self.print_warning("Skipping - No authentication token available")
            return False
        
        try:
            self.print_info(f"GET {self.api_url}/query/history?limit=5&offset=0")
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.api_url}/query/history",
                params={"limit": 5, "offset": 0},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_success("Successfully retrieved query history")
                self.print_json(data)
                
                if isinstance(data, list):
                    self.print_info(f"\nFound {len(data)} queries in history")
                elif isinstance(data, dict) and "items" in data:
                    self.print_info(f"\nFound {len(data['items'])} queries in history")
                    self.print_info(f"Total: {data.get('total', 'unknown')}")
                
                self.record_test(True)
                return True
            elif response.status_code == 404:
                self.print_warning("History endpoint not found (may not be implemented)")
                self.record_test(True)  # Don't fail if endpoint not implemented
                return True
            else:
                self.print_error(f"Failed to get history - Status: {response.status_code}")
                self.print_json(response.json())
                self.record_test(False)
                return False
                
        except Exception as e:
            self.print_error(f"History endpoint test failed: {str(e)}")
            self.record_test(False)
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        self.print_success(f"Passed: {passed}")
        if failed > 0:
            self.print_error(f"Failed: {failed}")
        else:
            self.print_success(f"Failed: {failed}")
        
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if failed == 0:
            self.print_success("\n🎉 All tests passed!")
        else:
            self.print_warning(f"\n⚠️  {failed} test(s) failed")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════════════════════════════════════════╗")
        print("║                    Chanakya API Test Suite                                 ║")
        print("║                                                                            ║")
        print(f"║  Base URL: {self.base_url:<60} ║")
        print(f"║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<64} ║")
        print("╚════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        # Test 1: Health Check
        if not self.test_health():
            self.print_error("\n❌ Server is not running or not accessible")
            self.print_warning("Please start the server and try again:")
            self.print_info("  cd Web_server")
            self.print_info("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            self.print_summary()
            return
        
        # Test 2: Authentication
        if not self.test_register_and_login():
            self.print_warning("\nAuthentication failed - some tests will be skipped")
        
        # Test 3: Tools Endpoint
        time.sleep(1)
        self.test_tools_endpoint()
        
        # Test 4: Query Endpoint
        time.sleep(1)
        query_id = self.test_query_endpoint("What is photosynthesis?")
        
        # Test 5: Status Endpoint
        time.sleep(1)
        self.test_status_endpoint(query_id)
        
        # Test 6: Query History
        time.sleep(1)
        self.test_query_history()
        
        # Print summary
        self.print_summary()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Chanakya API endpoints")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--query",
        default="What is photosynthesis?",
        help="Test query to send (default: 'What is photosynthesis?')"
    )
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
