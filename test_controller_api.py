#!/usr/bin/env python3
"""
Test script for the new Controller API endpoints
"""
import requests
import json
import time

# Configuration
BASE_URL = 'http://localhost:5000/api'
TEST_SERIAL = 'TEST001'
TEST_CONTROLLER = {
    'serial_number': TEST_SERIAL,
    'type': 'speedradar',
    'name': 'Test Speed Radar',
    'latitude': 52.3676,
    'longitude': 4.9041
}

def test_controller_registration():
    """Test controller registration"""
    print("Testing controller registration...")
    
    response = requests.post(f'{BASE_URL}/controllers/register', 
                           json=TEST_CONTROLLER)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 201

def test_controller_data_update():
    """Test controller data update"""
    print("\nTesting controller data update...")
    
    test_data = {
        'temperature': 22.5,
        'humidity': 65.3,
        'speed': 45.2,
        'direction': 'north'
    }
    
    response = requests.post(f'{BASE_URL}/controllers/{TEST_SERIAL}/data',
                           json=test_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_controller_status_update():
    """Test controller status update"""
    print("\nTesting controller status update...")
    
    status_data = {
        'online': True
    }
    
    response = requests.post(f'{BASE_URL}/controllers/{TEST_SERIAL}/status',
                           json=status_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_controller_modification():
    """Test controller modification"""
    print("\nTesting controller modification...")
    
    update_data = {
        'name': 'Updated Test Radar',
        'latitude': 52.3700,
        'longitude': 4.9100
    }
    
    response = requests.put(f'{BASE_URL}/controllers/{TEST_SERIAL}',
                          json=update_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_controller_info():
    """Test getting controller info"""
    print("\nTesting controller info retrieval...")
    
    response = requests.get(f'{BASE_URL}/controllers/{TEST_SERIAL}')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def main():
    """Run all tests"""
    print("=== Controller API Test Suite ===")
    print("Make sure the LXCloud server is running on localhost:5000")
    print()
    
    tests = [
        ("Controller Registration", test_controller_registration),
        ("Data Update", test_controller_data_update),
        ("Status Update", test_controller_status_update),
        ("Controller Modification", test_controller_modification),
        ("Controller Info", test_controller_info)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Could not connect to server at {BASE_URL}")
            print("Make sure the LXCloud server is running.")
            return
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            results.append((test_name, False))
        
        time.sleep(0.5)  # Small delay between tests
    
    print("\n=== Test Results ===")
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

if __name__ == '__main__':
    main()