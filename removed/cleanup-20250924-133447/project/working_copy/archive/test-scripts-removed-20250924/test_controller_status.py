#!/usr/bin/env python3
"""
Test script for controller status timeout functionality
"""
import sys
import os
import time
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config


def test_controller_timeout():
    """Test that controllers are marked offline after timeout"""
    app = create_app()

    with app.app_context():
        # Create test controller
        test_controller = Controller(
            serial_number="TEST_TIMEOUT_001",
            controller_type="speedradar",
            name="Test Timeout Controller",
            is_online=True,
            last_seen=datetime.utcnow()
            - timedelta(
                seconds=Config.CONTROLLER_OFFLINE_TIMEOUT + 60
            ),  # 1 minute past timeout
        )

        # Clean up any existing test controller
        existing = Controller.query.filter_by(serial_number="TEST_TIMEOUT_001").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        db.session.add(test_controller)
        db.session.commit()

        print(f"Created test controller: {test_controller.serial_number}")
        print(f"Last seen: {test_controller.last_seen}")
        print(f"Is online: {test_controller.is_online}")
        print(f"Timeout threshold: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds")

        # Initialize and force a status check
        controller_status_service.init_app(app)
        print("\nRunning status check...")
        controller_status_service.force_check()

        # Refresh the controller from database
        db.session.refresh(test_controller)

        print(f"\nAfter status check:")
        print(f"Is online: {test_controller.is_online}")

        # Clean up
        db.session.delete(test_controller)
        db.session.commit()

        # Verify result
        if not test_controller.is_online:
            print("✅ TEST PASSED: Controller was marked offline after timeout")
            return True
        else:
            print("❌ TEST FAILED: Controller was not marked offline")
            return False


def test_controller_within_timeout():
    """Test that controllers remain online when within timeout"""
    app = create_app()

    with app.app_context():
        # Create test controller with recent last_seen
        test_controller = Controller(
            serial_number="TEST_ONLINE_001",
            controller_type="speedradar",
            name="Test Online Controller",
            is_online=True,
            last_seen=datetime.utcnow()
            - timedelta(seconds=60),  # 1 minute ago (within timeout)
        )

        # Clean up any existing test controller
        existing = Controller.query.filter_by(serial_number="TEST_ONLINE_001").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        db.session.add(test_controller)
        db.session.commit()

        print(f"\nCreated test controller: {test_controller.serial_number}")
        print(f"Last seen: {test_controller.last_seen}")
        print(f"Is online: {test_controller.is_online}")

        # Initialize and force a status check
        controller_status_service.init_app(app)
        print("\nRunning status check...")
        controller_status_service.force_check()

        # Refresh the controller from database
        db.session.refresh(test_controller)

        print(f"\nAfter status check:")
        print(f"Is online: {test_controller.is_online}")

        # Clean up
        db.session.delete(test_controller)
        db.session.commit()

        # Verify result
        if test_controller.is_online:
            print("✅ TEST PASSED: Controller remained online within timeout")
            return True
        else:
            print("❌ TEST FAILED: Controller was incorrectly marked offline")
            return False


def main():
    """Run all tests"""
    print("=== Controller Status Timeout Test Suite ===")
    print(f"Configuration:")
    print(f"  CONTROLLER_OFFLINE_TIMEOUT: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds")
    print(
        f"  CONTROLLER_STATUS_CHECK_INTERVAL: {Config.CONTROLLER_STATUS_CHECK_INTERVAL} seconds"
    )
    print()

    tests = [
        ("Controller Offline After Timeout", test_controller_timeout),
        ("Controller Online Within Timeout", test_controller_within_timeout),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    print("\n=== Test Results ===")
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
Test script for controller status timeout functionality
"""
import sys
import os
import time
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Controller
from app.controller_status_service import controller_status_service
from config.config import Config


def test_controller_timeout():
    """Test that controllers are marked offline after timeout"""
    app = create_app()

    with app.app_context():
        # Create test controller
        test_controller = Controller(
            serial_number="TEST_TIMEOUT_001",
            controller_type="speedradar",
            name="Test Timeout Controller",
            is_online=True,
            last_seen=datetime.utcnow()
            - timedelta(
                seconds=Config.CONTROLLER_OFFLINE_TIMEOUT + 60
            ),  # 1 minute past timeout
        )

        # Clean up any existing test controller
        existing = Controller.query.filter_by(serial_number="TEST_TIMEOUT_001").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        db.session.add(test_controller)
        db.session.commit()

        print(f"Created test controller: {test_controller.serial_number}")
        print(f"Last seen: {test_controller.last_seen}")
        print(f"Is online: {test_controller.is_online}")
        print(f"Timeout threshold: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds")

        # Initialize and force a status check
        controller_status_service.init_app(app)
        print("\nRunning status check...")
        controller_status_service.force_check()

        # Refresh the controller from database
        db.session.refresh(test_controller)

        print(f"\nAfter status check:")
        print(f"Is online: {test_controller.is_online}")

        # Clean up
        db.session.delete(test_controller)
        db.session.commit()

        # Verify result
        if not test_controller.is_online:
            print("✅ TEST PASSED: Controller was marked offline after timeout")
            return True
        else:
            print("❌ TEST FAILED: Controller was not marked offline")
            return False


def test_controller_within_timeout():
    """Test that controllers remain online when within timeout"""
    app = create_app()

    with app.app_context():
        # Create test controller with recent last_seen
        test_controller = Controller(
            serial_number="TEST_ONLINE_001",
            controller_type="speedradar",
            name="Test Online Controller",
            is_online=True,
            last_seen=datetime.utcnow()
            - timedelta(seconds=60),  # 1 minute ago (within timeout)
        )

        # Clean up any existing test controller
        existing = Controller.query.filter_by(serial_number="TEST_ONLINE_001").first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        db.session.add(test_controller)
        db.session.commit()

        print(f"\nCreated test controller: {test_controller.serial_number}")
        print(f"Last seen: {test_controller.last_seen}")
        print(f"Is online: {test_controller.is_online}")

        # Initialize and force a status check
        controller_status_service.init_app(app)
        print("\nRunning status check...")
        controller_status_service.force_check()

        # Refresh the controller from database
        db.session.refresh(test_controller)

        print(f"\nAfter status check:")
        print(f"Is online: {test_controller.is_online}")

        # Clean up
        db.session.delete(test_controller)
        db.session.commit()

        # Verify result
        if test_controller.is_online:
            print("✅ TEST PASSED: Controller remained online within timeout")
            return True
        else:
            print("❌ TEST FAILED: Controller was incorrectly marked offline")
            return False


def main():
    """Run all tests"""
    print("=== Controller Status Timeout Test Suite ===")
    print(f"Configuration:")
    print(f"  CONTROLLER_OFFLINE_TIMEOUT: {Config.CONTROLLER_OFFLINE_TIMEOUT} seconds")
    print(
        f"  CONTROLLER_STATUS_CHECK_INTERVAL: {Config.CONTROLLER_STATUS_CHECK_INTERVAL} seconds"
    )
    print()

    tests = [
        ("Controller Offline After Timeout", test_controller_timeout),
        ("Controller Online Within Timeout", test_controller_within_timeout),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"ERROR in {test_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    print("\n=== Test Results ===")
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
