#!/usr/bin/env python3
"""
Simple test to verify API authentication is working
"""

import sys
import os
import requests
import time
import subprocess
from threading import Thread

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_app():
    """Start the Flask app in background"""
    subprocess.run(
        [sys.executable, "run.py"], cwd=os.path.dirname(os.path.abspath(__file__))
    )


def test_api_auth():
    """Test that API endpoints require authentication"""

    print("Testing API Authentication")
    print("=" * 30)

    # Start app in background
    app_thread = Thread(target=start_app, daemon=True)
    app_thread.start()

    # Wait for app to start
    print("Waiting for app to start...")
    time.sleep(5)

    base_url = "http://127.0.0.1:5000"

    # Test 1: Unauthenticated access should be denied
    print("\n1. Testing unauthenticated access...")

    try:
        response = requests.get(f"{base_url}/api/map-data", allow_redirects=False)
        print(f"   /api/map-data without auth: {response.status_code}")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        assert "/auth/login" in response.headers.get(
            "Location", ""
        ), "Should redirect to login"

        response = requests.get(
            f"{base_url}/api/controllers/list", allow_redirects=False
        )
        print(f"   /api/controllers/list without auth: {response.status_code}")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        assert "/auth/login" in response.headers.get(
            "Location", ""
        ), "Should redirect to login"

        print("   ✅ Both endpoints correctly require authentication")

    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to app - it may not have started properly")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

    # Test 2: Login and check authenticated access
    print("\n2. Testing authenticated access...")

    try:
        session = requests.Session()

        # Get login page to get any CSRF tokens
        login_page = session.get(f"{base_url}/auth/login")

        # Login with default admin credentials
        login_data = {"username": "admin", "password": "admin123"}

        login_response = session.post(
            f"{base_url}/auth/login", data=login_data, allow_redirects=True
        )

        if login_response.status_code == 200 and (
            "dashboard" in login_response.url or login_response.url.endswith("/")
        ):
            print("   ✅ Successfully logged in as admin")

            # Test authenticated API access
            response = session.get(f"{base_url}/api/map-data")
            print(f"   /api/map-data with auth: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ Authenticated access to /api/map-data works")
                try:
                    data = response.json()
                    print(f"   Admin can see {len(data)} controllers on map")
                except:
                    print("   ✅ Response is valid (may be empty list)")
            else:
                print(f"   ❌ Expected 200, got {response.status_code}")
                return False

            response = session.get(f"{base_url}/api/controllers/list")
            print(f"   /api/controllers/list with auth: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ Authenticated access to /api/controllers/list works")
                try:
                    data = response.json()
                    print(
                        f"   Admin can see {len(data.get('controllers', []))} controllers in list"
                    )
                except:
                    print("   ✅ Response is valid (may be empty list)")
            else:
                print(f"   ❌ Expected 200, got {response.status_code}")
                return False
        else:
            print(
                f"   ❌ Login failed: {login_response.status_code} - {login_response.url}"
            )
            return False

    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

    print("\n✅ All authentication tests passed!")
    print("\nSummary:")
    print("- Unauthenticated users are properly redirected to login")
    print("- Authenticated users can access the API endpoints")
    print("- Both /api/map-data and /api/controllers/list are properly secured")

    return True


if __name__ == "__main__":
    success = test_api_auth()
    if not success:
        sys.exit(1)
#!/usr/bin/env python3
"""
Simple test to verify API authentication is working
"""

import sys
import os
import requests
import time
import subprocess
from threading import Thread

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_app():
    """Start the Flask app in background"""
    subprocess.run(
        [sys.executable, "run.py"], cwd=os.path.dirname(os.path.abspath(__file__))
    )


def test_api_auth():
    """Test that API endpoints require authentication"""

    print("Testing API Authentication")
    print("=" * 30)

    # Start app in background
    app_thread = Thread(target=start_app, daemon=True)
    app_thread.start()

    # Wait for app to start
    print("Waiting for app to start...")
    time.sleep(5)

    base_url = "http://127.0.0.1:5000"

    # Test 1: Unauthenticated access should be denied
    print("\n1. Testing unauthenticated access...")

    try:
        response = requests.get(f"{base_url}/api/map-data", allow_redirects=False)
        print(f"   /api/map-data without auth: {response.status_code}")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        assert "/auth/login" in response.headers.get(
            "Location", ""
        ), "Should redirect to login"

        response = requests.get(
            f"{base_url}/api/controllers/list", allow_redirects=False
        )
        print(f"   /api/controllers/list without auth: {response.status_code}")
        assert response.status_code == 302, f"Expected 302, got {response.status_code}"
        assert "/auth/login" in response.headers.get(
            "Location", ""
        ), "Should redirect to login"

        print("   ✅ Both endpoints correctly require authentication")

    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to app - it may not have started properly")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

    # Test 2: Login and check authenticated access
    print("\n2. Testing authenticated access...")

    try:
        session = requests.Session()

        # Get login page to get any CSRF tokens
        login_page = session.get(f"{base_url}/auth/login")

        # Login with default admin credentials
        login_data = {"username": "admin", "password": "admin123"}

        login_response = session.post(
            f"{base_url}/auth/login", data=login_data, allow_redirects=True
        )

        if login_response.status_code == 200 and (
            "dashboard" in login_response.url or login_response.url.endswith("/")
        ):
            print("   ✅ Successfully logged in as admin")

            # Test authenticated API access
            response = session.get(f"{base_url}/api/map-data")
            print(f"   /api/map-data with auth: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ Authenticated access to /api/map-data works")
                try:
                    data = response.json()
                    print(f"   Admin can see {len(data)} controllers on map")
                except:
                    print("   ✅ Response is valid (may be empty list)")
            else:
                print(f"   ❌ Expected 200, got {response.status_code}")
                return False

            response = session.get(f"{base_url}/api/controllers/list")
            print(f"   /api/controllers/list with auth: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ Authenticated access to /api/controllers/list works")
                try:
                    data = response.json()
                    print(
                        f"   Admin can see {len(data.get('controllers', []))} controllers in list"
                    )
                except:
                    print("   ✅ Response is valid (may be empty list)")
            else:
                print(f"   ❌ Expected 200, got {response.status_code}")
                return False
        else:
            print(
                f"   ❌ Login failed: {login_response.status_code} - {login_response.url}"
            )
            return False

    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
        return False

    print("\n✅ All authentication tests passed!")
    print("\nSummary:")
    print("- Unauthenticated users are properly redirected to login")
    print("- Authenticated users can access the API endpoints")
    print("- Both /api/map-data and /api/controllers/list are properly secured")

    return True


if __name__ == "__main__":
    success = test_api_auth()
    if not success:
        sys.exit(1)
