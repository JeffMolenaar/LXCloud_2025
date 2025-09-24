#!/usr/bin/env python3
"""
Test script to validate API authentication and user-specific data filtering
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Controller
from config.config import Config


def test_api_authentication():
    """Test API endpoints for proper authentication and data filtering"""

    # Create test app with in-memory SQLite
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        # Initialize database
        db.create_all()

        # Use existing admin user or create if not exists
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(username="admin", email="admin@test.com", is_admin=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)

        # Create regular test user
        regular_user = User.query.filter_by(username="user1").first()
        if not regular_user:
            regular_user = User(
                username="user1", email="user1@test.com", is_admin=False
            )
            regular_user.set_password("user123")
            db.session.add(regular_user)

        db.session.commit()

        # Create test controllers
        controller1 = Controller(
            serial_number="CTRL001",
            controller_type="speedradar",
            name="User1 Controller",
            user_id=regular_user.id,
            latitude=52.0,
            longitude=4.0,
            is_online=True,
            last_seen=datetime.utcnow(),
        )

        controller2 = Controller(
            serial_number="CTRL002",
            controller_type="weatherstation",
            name="Admin Controller",
            user_id=admin_user.id,
            latitude=53.0,
            longitude=5.0,
            is_online=False,
            last_seen=datetime.utcnow(),
        )

        controller3 = Controller(
            serial_number="CTRL003",
            controller_type="beaufortmeter",
            name="Unbound Controller",
            user_id=None,  # Unbound controller
            latitude=54.0,
            longitude=6.0,
            is_online=True,
            last_seen=datetime.utcnow(),
        )

        db.session.add(controller1)
        db.session.add(controller2)
        db.session.add(controller3)
        db.session.commit()

        client = app.test_client()

        print("Testing API Authentication and Data Filtering")
        print("=" * 50)

        # Test 1: Unauthenticated access should be denied
        print("\n1. Testing unauthenticated access...")

        response = client.get("/api/map-data")
        print(f"   /api/map-data without auth: {response.status_code}")
        assert response.status_code == 302  # Redirect to login

        response = client.get("/api/controllers/list")
        print(f"   /api/controllers/list without auth: {response.status_code}")
        assert response.status_code == 302  # Redirect to login

        # Test 2: Regular user should see only their controllers
        print("\n2. Testing regular user access...")

        # Login as regular user
        response = client.post(
            "/auth/login",
            data={"username": "user1", "password": "user123"},
            follow_redirects=True,
        )

        response = client.get("/api/map-data")
        print(f"   /api/map-data for regular user: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        print(f"   Regular user sees {len(data)} controllers on map")
        assert len(data) == 1  # Should only see their own controller
        assert data[0]["serial_number"] == "CTRL001"

        response = client.get("/api/controllers/list")
        print(f"   /api/controllers/list for regular user: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        controllers = data["controllers"]
        print(f"   Regular user sees {len(controllers)} controllers in list")
        assert len(controllers) == 1  # Should only see their own controller
        assert controllers[0]["serial_number"] == "CTRL001"

        # Test 3: Admin user should see all controllers
        print("\n3. Testing admin user access...")

        # Logout and login as admin
        client.get("/auth/logout")
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )

        response = client.get("/api/map-data")
        print(f"   /api/map-data for admin: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        print(f"   Admin sees {len(data)} controllers on map")
        assert len(data) == 3  # Should see all controllers with location data
        serials = [c["serial_number"] for c in data]
        assert "CTRL001" in serials
        assert "CTRL002" in serials
        assert "CTRL003" in serials

        response = client.get("/api/controllers/list")
        print(f"   /api/controllers/list for admin: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        controllers = data["controllers"]
        print(f"   Admin sees {len(controllers)} controllers in list")
        assert len(controllers) == 3  # Should see all controllers
        serials = [c["serial_number"] for c in controllers]
        assert "CTRL001" in serials
        assert "CTRL002" in serials
        assert "CTRL003" in serials

        print(
            "\n✅ All tests passed! API authentication and filtering works correctly."
        )
        print("\nSummary:")
        print("- Unauthenticated users are redirected to login")
        print("- Regular users see only their bound controllers")
        print("- Admin users see all controllers")
        print("- Both map-data and controllers/list endpoints are properly secured")


if __name__ == "__main__":
    test_api_authentication()
#!/usr/bin/env python3
"""
Test script to validate API authentication and user-specific data filtering
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User, Controller
from config.config import Config


def test_api_authentication():
    """Test API endpoints for proper authentication and data filtering"""

    # Create test app with in-memory SQLite
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        # Initialize database
        db.create_all()

        # Use existing admin user or create if not exists
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin_user = User(username="admin", email="admin@test.com", is_admin=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)

        # Create regular test user
        regular_user = User.query.filter_by(username="user1").first()
        if not regular_user:
            regular_user = User(
                username="user1", email="user1@test.com", is_admin=False
            )
            regular_user.set_password("user123")
            db.session.add(regular_user)

        db.session.commit()

        # Create test controllers
        controller1 = Controller(
            serial_number="CTRL001",
            controller_type="speedradar",
            name="User1 Controller",
            user_id=regular_user.id,
            latitude=52.0,
            longitude=4.0,
            is_online=True,
            last_seen=datetime.utcnow(),
        )

        controller2 = Controller(
            serial_number="CTRL002",
            controller_type="weatherstation",
            name="Admin Controller",
            user_id=admin_user.id,
            latitude=53.0,
            longitude=5.0,
            is_online=False,
            last_seen=datetime.utcnow(),
        )

        controller3 = Controller(
            serial_number="CTRL003",
            controller_type="beaufortmeter",
            name="Unbound Controller",
            user_id=None,  # Unbound controller
            latitude=54.0,
            longitude=6.0,
            is_online=True,
            last_seen=datetime.utcnow(),
        )

        db.session.add(controller1)
        db.session.add(controller2)
        db.session.add(controller3)
        db.session.commit()

        client = app.test_client()

        print("Testing API Authentication and Data Filtering")
        print("=" * 50)

        # Test 1: Unauthenticated access should be denied
        print("\n1. Testing unauthenticated access...")

        response = client.get("/api/map-data")
        print(f"   /api/map-data without auth: {response.status_code}")
        assert response.status_code == 302  # Redirect to login

        response = client.get("/api/controllers/list")
        print(f"   /api/controllers/list without auth: {response.status_code}")
        assert response.status_code == 302  # Redirect to login

        # Test 2: Regular user should see only their controllers
        print("\n2. Testing regular user access...")

        # Login as regular user
        response = client.post(
            "/auth/login",
            data={"username": "user1", "password": "user123"},
            follow_redirects=True,
        )

        response = client.get("/api/map-data")
        print(f"   /api/map-data for regular user: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        print(f"   Regular user sees {len(data)} controllers on map")
        assert len(data) == 1  # Should only see their own controller
        assert data[0]["serial_number"] == "CTRL001"

        response = client.get("/api/controllers/list")
        print(f"   /api/controllers/list for regular user: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        controllers = data["controllers"]
        print(f"   Regular user sees {len(controllers)} controllers in list")
        assert len(controllers) == 1  # Should only see their own controller
        assert controllers[0]["serial_number"] == "CTRL001"

        # Test 3: Admin user should see all controllers
        print("\n3. Testing admin user access...")

        # Logout and login as admin
        client.get("/auth/logout")
        response = client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )

        response = client.get("/api/map-data")
        print(f"   /api/map-data for admin: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        print(f"   Admin sees {len(data)} controllers on map")
        assert len(data) == 3  # Should see all controllers with location data
        serials = [c["serial_number"] for c in data]
        assert "CTRL001" in serials
        assert "CTRL002" in serials
        assert "CTRL003" in serials

        response = client.get("/api/controllers/list")
        print(f"   /api/controllers/list for admin: {response.status_code}")
        assert response.status_code == 200

        data = response.get_json()
        controllers = data["controllers"]
        print(f"   Admin sees {len(controllers)} controllers in list")
        assert len(controllers) == 3  # Should see all controllers
        serials = [c["serial_number"] for c in controllers]
        assert "CTRL001" in serials
        assert "CTRL002" in serials
        assert "CTRL003" in serials

        print(
            "\n✅ All tests passed! API authentication and filtering works correctly."
        )
        print("\nSummary:")
        print("- Unauthenticated users are redirected to login")
        print("- Regular users see only their bound controllers")
        print("- Admin users see all controllers")
        print("- Both map-data and controllers/list endpoints are properly secured")


if __name__ == "__main__":
    test_api_authentication()
