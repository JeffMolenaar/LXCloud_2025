#!/usr/bin/env python3
"""
Standalone migration script to add marker_config column to ui_customization table
This script specifically addresses the missing marker_config column issue
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database_config import DatabaseConfig


def migrate_marker_config():
    """Add marker_config column to ui_customization table if it doesn't exist"""
    print("🔄 Migrating ui_customization table to add marker_config column")
    print("=" * 60)
    
    config = DatabaseConfig()
    config.print_config()
    print()
    
    try:
        # Test connection first
        if not config.test_connection():
            print("❌ Database connection failed. Cannot perform migration.")
            return False
        
        # Create connection
        conn = config.create_connection()
        cursor = conn.cursor()
        
        print("🔍 Checking current table structure...")
        
        # Check if ui_customization table exists
        cursor.execute("SHOW TABLES LIKE 'ui_customization'")
        if not cursor.fetchone():
            print("❌ ui_customization table does not exist. Please run database initialization first.")
            print("   Run: python database_utils.py init")
            return False
        
        # Check current columns
        cursor.execute("DESCRIBE ui_customization")
        columns = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Current columns in ui_customization table:")
        for i, col in enumerate(columns, 1):
            print(f"   {i}. {col}")
        
        # Check if marker_config column exists
        if 'marker_config' in columns:
            print("✅ marker_config column already exists. No migration needed.")
            return True
        
        print("\n🔧 Adding marker_config column...")
        
        # Add the column
        cursor.execute("ALTER TABLE ui_customization ADD COLUMN marker_config TEXT")
        conn.commit()
        
        print("✅ Successfully added marker_config column!")
        
        # Verify the addition
        cursor.execute("DESCRIBE ui_customization")
        new_columns = [row[0] for row in cursor.fetchall()]
        
        if 'marker_config' in new_columns:
            print("✅ Migration verified: marker_config column is now present")
            print(f"📋 Updated table structure:")
            for i, col in enumerate(new_columns, 1):
                marker = " (NEW)" if col == 'marker_config' else ""
                print(f"   {i}. {col}{marker}")
        else:
            print("❌ Migration verification failed: marker_config column not found")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        
        # Additional error information for common issues
        if "Unknown column" in str(e):
            print("\n💡 This error suggests the column we're trying to query doesn't exist.")
            print("   This is actually the problem we're trying to fix!")
        elif "Access denied" in str(e):
            print("\n💡 Database user doesn't have ALTER privileges.")
            print("   You may need to run this with a database admin user.")
        elif "Connection refused" in str(e):
            print("\n💡 Database server is not running or not accessible.")
            print("   Please check if MariaDB/MySQL is running.")
        
        return False


def test_marker_config_functionality():
    """Test that the marker_config functionality works after migration"""
    print("\n🧪 Testing marker_config functionality...")
    
    try:
        from app import create_app
        from app.models import db, UICustomization
        
        app = create_app()
        with app.app_context():
            # Try to create a test customization with marker config
            test_customization = UICustomization.query.filter_by(page_name='test_migration').first()
            
            if not test_customization:
                test_customization = UICustomization(page_name='test_migration')
                db.session.add(test_customization)
            
            # Test setting marker config
            test_config = {
                'speedradar': {
                    'online': {'icon': 'fas fa-tachometer-alt', 'color': '#28a745', 'size': '30'},
                    'offline': {'icon': 'fas fa-tachometer-alt', 'color': '#dc3545', 'size': '30'}
                }
            }
            
            test_customization.set_marker_config(test_config)
            db.session.commit()
            
            # Test getting marker config
            retrieved_config = test_customization.get_marker_config()
            
            if retrieved_config == test_config:
                print("✅ marker_config functionality test passed!")
                
                # Clean up test data
                db.session.delete(test_customization)
                db.session.commit()
                return True
            else:
                print("❌ marker_config functionality test failed!")
                print(f"   Expected: {test_config}")
                print(f"   Got: {retrieved_config}")
                return False
                
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False


def main():
    """Main function"""
    print("LXCloud marker_config Migration Tool")
    print("=" * 60)
    print()
    
    # Perform migration
    if migrate_marker_config():
        print("\n🎉 Migration completed successfully!")
        
        # Test functionality
        if test_marker_config_functionality():
            print("\n✅ All tests passed. The marker_config column is working correctly.")
            print("\n📝 Next steps:")
            print("   1. Restart your LXCloud application")
            print("   2. The UI customization error should now be resolved")
            print("   3. You can configure marker settings in Admin → UI Customization")
        else:
            print("\n⚠️  Migration succeeded but functionality test failed.")
            print("   The column was added but there may be application-level issues.")
        
        return True
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure MariaDB/MySQL is running")
        print("   2. Verify database credentials are correct")
        print("   3. Check that the database user has ALTER privileges")
        print("   4. Consider running: python database_utils.py test")
        
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)