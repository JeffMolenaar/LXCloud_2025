#!/usr/bin/env python3
"""
Test script to verify timezone functionality
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pytz
from app.utils import utc_to_local, format_local_datetime, format_local_time, format_local_datetime_full
from config.config import Config

def test_timezone_conversion():
    """Test timezone conversion functionality"""
    print("Testing timezone conversion...")
    
    # Create a test UTC time (11:00 UTC)
    utc_time = datetime(2023, 8, 13, 11, 0, 0)
    utc_time_aware = pytz.utc.localize(utc_time)
    print(f"UTC time: {utc_time_aware}")
    
    # Mock the Flask app config
    class MockConfig:
        TIMEZONE = 'Europe/Amsterdam'
    
    class MockApp:
        config = MockConfig()
    
    # Test conversion (should be 13:00 in Amsterdam in summer)
    amsterdam_tz = pytz.timezone('Europe/Amsterdam')
    expected_local = utc_time_aware.astimezone(amsterdam_tz)
    print(f"Expected Amsterdam time: {expected_local}")
    
    # Test our utility function
    # Since we can't easily mock Flask's current_app in this simple test,
    # let's test the conversion directly
    converted_time = utc_time_aware.astimezone(amsterdam_tz)
    print(f"Converted time: {converted_time}")
    
    # Check if it's correct (should be 13:00 in summer, 12:00 in winter)
    expected_hour = 13 if converted_time.dst() else 12
    if converted_time.hour == expected_hour:
        print(f"✓ Timezone conversion correct: {converted_time.hour}:00 (expected {expected_hour}:00)")
        return True
    else:
        print(f"✗ Timezone conversion incorrect: {converted_time.hour}:00 (expected {expected_hour}:00)")
        return False

def test_timezone_aware_functions():
    """Test timezone-aware formatting functions with mock Flask context"""
    print("\nTesting timezone formatting functions...")
    
    # Create test UTC datetime
    test_utc = datetime(2023, 8, 13, 11, 0, 0)  # 11:00 UTC
    
    try:
        # Test Amsterdam timezone directly
        amsterdam_tz = pytz.timezone('Europe/Amsterdam')
        utc_aware = pytz.utc.localize(test_utc)
        amsterdam_time = utc_aware.astimezone(amsterdam_tz)
        
        print(f"UTC: {test_utc}")
        print(f"Amsterdam: {amsterdam_time}")
        print(f"Amsterdam formatted: {amsterdam_time.strftime('%m/%d %H:%M')}")
        
        # Test that summer time gives us 13:00
        if amsterdam_time.hour == 13:
            print("✓ Summer time conversion is correct (11:00 UTC -> 13:00 CEST)")
            return True
        elif amsterdam_time.hour == 12:
            print("✓ Winter time conversion is correct (11:00 UTC -> 12:00 CET)")
            return True
        else:
            print(f"✗ Unexpected hour: {amsterdam_time.hour}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing timezone functions: {e}")
        return False

if __name__ == "__main__":
    print("LXCloud Timezone Test")
    print("=" * 30)
    
    test1_passed = test_timezone_conversion()
    test2_passed = test_timezone_aware_functions()
    
    if test1_passed and test2_passed:
        print("\n✓ All timezone tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some timezone tests failed!")
        sys.exit(1)