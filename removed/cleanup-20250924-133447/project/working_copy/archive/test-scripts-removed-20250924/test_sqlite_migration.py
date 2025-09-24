#!/usr/bin/env python3
"""
SQLite version of the marker_config migration for testing
"""
import sqlite3
import sys
import os


def migrate_sqlite_marker_config(db_path):
    """Add marker_config column to ui_customization table in SQLite database"""
    print(f"🔄 Migrating SQLite database: {db_path}")
    print("=" * 60)

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔍 Checking current table structure...")

        # Check if ui_customization table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ui_customization'"
        )
        if not cursor.fetchone():
            print("❌ ui_customization table does not exist.")
            return False

        # Check current columns
        cursor.execute("PRAGMA table_info(ui_customization)")
        columns = [row[1] for row in cursor.fetchall()]

        print(f"📋 Current columns in ui_customization table:")
        for i, col in enumerate(columns, 1):
            print(f"   {i}. {col}")

        # Check if marker_config column exists
        if "marker_config" in columns:
            print("✅ marker_config column already exists. No migration needed.")
            return True

        print("\n🔧 Adding marker_config column...")

        # Add the column
        cursor.execute("ALTER TABLE ui_customization ADD COLUMN marker_config TEXT")
        conn.commit()

        print("✅ Successfully added marker_config column!")

        # Verify the addition
        cursor.execute("PRAGMA table_info(ui_customization)")
        new_columns = [row[1] for row in cursor.fetchall()]

        if "marker_config" in new_columns:
            print("✅ Migration verified: marker_config column is now present")
            print(f"📋 Updated table structure:")
            for i, col in enumerate(new_columns, 1):
                marker = " (NEW)" if col == "marker_config" else ""
                print(f"   {i}. {col}{marker}")
        else:
            print("❌ Migration verification failed: marker_config column not found")
            return False

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_sqlite_migration.py <database_path>")
        sys.exit(1)

    db_path = sys.argv[1]
    success = migrate_sqlite_marker_config(db_path)
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
SQLite version of the marker_config migration for testing
"""
import sqlite3
import sys
import os


def migrate_sqlite_marker_config(db_path):
    """Add marker_config column to ui_customization table in SQLite database"""
    print(f"🔄 Migrating SQLite database: {db_path}")
    print("=" * 60)

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔍 Checking current table structure...")

        # Check if ui_customization table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ui_customization'"
        )
        if not cursor.fetchone():
            print("❌ ui_customization table does not exist.")
            return False

        # Check current columns
        cursor.execute("PRAGMA table_info(ui_customization)")
        columns = [row[1] for row in cursor.fetchall()]

        print(f"📋 Current columns in ui_customization table:")
        for i, col in enumerate(columns, 1):
            print(f"   {i}. {col}")

        # Check if marker_config column exists
        if "marker_config" in columns:
            print("✅ marker_config column already exists. No migration needed.")
            return True

        print("\n🔧 Adding marker_config column...")

        # Add the column
        cursor.execute("ALTER TABLE ui_customization ADD COLUMN marker_config TEXT")
        conn.commit()

        print("✅ Successfully added marker_config column!")

        # Verify the addition
        cursor.execute("PRAGMA table_info(ui_customization)")
        new_columns = [row[1] for row in cursor.fetchall()]

        if "marker_config" in new_columns:
            print("✅ Migration verified: marker_config column is now present")
            print(f"📋 Updated table structure:")
            for i, col in enumerate(new_columns, 1):
                marker = " (NEW)" if col == "marker_config" else ""
                print(f"   {i}. {col}{marker}")
        else:
            print("❌ Migration verification failed: marker_config column not found")
            return False

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_sqlite_migration.py <database_path>")
        sys.exit(1)

    db_path = sys.argv[1]
    success = migrate_sqlite_marker_config(db_path)
    sys.exit(0 if success else 1)
