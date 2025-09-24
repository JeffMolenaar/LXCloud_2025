#!/usr/bin/env python3
"""
Integration test for controller status timeout with API endpoints
"""
import sys
import os
import time
import requests
import threading
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config

# Test configuration
TEST_PORT = 5001
BASE_URL = f"http://localhost:{TEST_PORT}/api"
TEST_SERIAL = "INTEGRATION_TEST_001"


def run_test_server():
    """Run a test server for integration testing"""
    app = create_app()

    # Initialize services
    controller_status_service.init_app(app)
    controller_status_service.start()

    # Run server in a separate thread
    app.run(host="127.0.0.1", port=TEST_PORT, debug=False, threaded=True)


def test_api_registration_sets_online():
    """Test that controller registration sets the controller online"""
    print("\n=== Testing API Controller Registration ===")

    # Register a controller
    controller_data = {
        "serial_number": TEST_SERIAL,
        "type": "speedradar",
        "name": "Integration Test Controller",
        "latitude": 52.3676,
        "longitude": 4.9041,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/controllers/register", json=controller_data, timeout=5
        )

        print(f"Registration response status: {response.status_code}")

        if response.status_code in [200, 201]:
            data = response.json()
            controller_info = data.get("controller", {})
            print(f"Controller is_online: {controller_info.get('is_online')}")
            print(f"Controller last_seen: {controller_info.get('last_seen')}")
            return controller_info.get("is_online") == True
        else:
            print(f"Registration failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def test_api_data_update_sets_online():
    """Test that data updates set the controller online"""
    print("\n=== Testing API Data Update ===")

    test_data = {
        "temperature": 22.5,
        "humidity": 65.3,
        "speed": 45.2,
        "direction": "north",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/controllers/{TEST_SERIAL}/data", json=test_data, timeout=5
        )

        print(f"Data update response status: {response.status_code}")

        if response.status_code == 200:
            print("Data update successful")
            return True
        else:
            print(f"Data update failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def test_controller_info_after_update():
    """Test getting controller info after updates"""
    print("\n=== Testing Controller Info Retrieval ===")

    try:
        response = requests.get(f"{BASE_URL}/controllers/{TEST_SERIAL}", timeout=5)

        print(f"Info retrieval response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            controller_info = data.get("controller", {})
            print(f"Controller is_online: {controller_info.get('is_online')}")
            print(f"Controller last_seen: {controller_info.get('last_seen')}")
            return controller_info.get("is_online") == True
        else:
            print(f"Info retrieval failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def wait_for_server():
    """Wait for test server to start"""
    print("Waiting for test server to start...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/controllers/debug", timeout=2)
            if response.status_code == 200:
                print("Test server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

    print("Test server failed to start within timeout")
    return False


def main():
    """Run integration tests"""
    print("=== Controller Status Integration Test Suite ===")
    print(f"Configuration:")
    print(f"  CONTROLLER_OFFLINE_TIMEOUT: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds")
    print(
        f"  CONTROLLER_STATUS_CHECK_INTERVAL: {Config.CONTROLLER_STATUS_CHECK_INTERVAL} seconds"
    )
    print(f"  Test server: {BASE_URL}")

    # Start test server in background thread
    server_thread = threading.Thread(target=run_test_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    if not wait_for_server():
        print("❌ Failed to start test server")
        return False

    # Run tests
    tests = [
        ("API Controller Registration Sets Online", test_api_registration_sets_online),
        ("API Data Update Maintains Online", test_api_data_update_sets_online),
        ("Controller Info Shows Online Status", test_controller_info_after_update),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            if not success:
                print(f"❌ {test_name}: FAILED")
            else:
                print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

        time.sleep(1)  # Small delay between tests

    print("\n=== Integration Test Results ===")
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Integration test for controller status timeout with API endpoints
"""
import sys
import os
import time
import requests
import threading
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config

# Test configuration
TEST_PORT = 5001
BASE_URL = f"http://localhost:{TEST_PORT}/api"
TEST_SERIAL = "INTEGRATION_TEST_001"


def run_test_server():
    """Run a test server for integration testing"""
    app = create_app()

    # Initialize services
    controller_status_service.init_app(app)
    controller_status_service.start()

    # Run server in a separate thread
    app.run(host="127.0.0.1", port=TEST_PORT, debug=False, threaded=True)


def test_api_registration_sets_online():
    """Test that controller registration sets the controller online"""
    print("\n=== Testing API Controller Registration ===")

    # Register a controller
    controller_data = {
        "serial_number": TEST_SERIAL,
        "type": "speedradar",
        "name": "Integration Test Controller",
        "latitude": 52.3676,
        "longitude": 4.9041,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/controllers/register", json=controller_data, timeout=5
        )

        print(f"Registration response status: {response.status_code}")

        if response.status_code in [200, 201]:
            data = response.json()
            controller_info = data.get("controller", {})
            print(f"Controller is_online: {controller_info.get('is_online')}")
            print(f"Controller last_seen: {controller_info.get('last_seen')}")
            return controller_info.get("is_online") == True
        else:
            print(f"Registration failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def test_api_data_update_sets_online():
    """Test that data updates set the controller online"""
    print("\n=== Testing API Data Update ===")

    test_data = {
        "temperature": 22.5,
        "humidity": 65.3,
        "speed": 45.2,
        "direction": "north",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/controllers/{TEST_SERIAL}/data", json=test_data, timeout=5
        )

        print(f"Data update response status: {response.status_code}")

        if response.status_code == 200:
            print("Data update successful")
            return True
        else:
            print(f"Data update failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def test_controller_info_after_update():
    """Test getting controller info after updates"""
    print("\n=== Testing Controller Info Retrieval ===")

    try:
        response = requests.get(f"{BASE_URL}/controllers/{TEST_SERIAL}", timeout=5)

        print(f"Info retrieval response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            controller_info = data.get("controller", {})
            print(f"Controller is_online: {controller_info.get('is_online')}")
            print(f"Controller last_seen: {controller_info.get('last_seen')}")
            return controller_info.get("is_online") == True
        else:
            print(f"Info retrieval failed: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False


def wait_for_server():
    """Wait for test server to start"""
    print("Waiting for test server to start...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/controllers/debug", timeout=2)
            if response.status_code == 200:
                print("Test server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)

    print("Test server failed to start within timeout")
    return False


def main():
    """Run integration tests"""
    print("=== Controller Status Integration Test Suite ===")
    print(f"Configuration:")
    print(f"  CONTROLLER_OFFLINE_TIMEOUT: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds")
    print(
        f"  CONTROLLER_STATUS_CHECK_INTERVAL: {Config.CONTROLLER_STATUS_CHECK_INTERVAL} seconds"
    )
    print(f"  Test server: {BASE_URL}")

    # Start test server in background thread
    server_thread = threading.Thread(target=run_test_server, daemon=True)
    server_thread.start()

    # Wait for server to be ready
    if not wait_for_server():
        print("❌ Failed to start test server")
        return False

    # Run tests
    tests = [
        ("API Controller Registration Sets Online", test_api_registration_sets_online),
        ("API Data Update Maintains Online", test_api_data_update_sets_online),
        ("Controller Info Shows Online Status", test_controller_info_after_update),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            if not success:
                print(f"❌ {test_name}: FAILED")
            else:
                print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

        time.sleep(1)  # Small delay between tests

    print("\n=== Integration Test Results ===")
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
