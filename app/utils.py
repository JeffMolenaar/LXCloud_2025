"""
Utility functions for LXCloud
"""
import pytz
from datetime import datetime
from flask import current_app


def get_local_timezone():
    """Get the configured local timezone"""
    timezone_name = current_app.config.get('TIMEZONE', 'Europe/Amsterdam')
    return pytz.timezone(timezone_name)


def utc_to_local(utc_dt):
    """Convert UTC datetime to local timezone"""
    if utc_dt is None:
        return None
    
    # If datetime is not timezone-aware, assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    
    local_tz = get_local_timezone()
    return utc_dt.astimezone(local_tz)


def format_local_datetime(utc_dt, format_str='%m/%d %H:%M'):
    """Convert UTC datetime to local timezone and format it"""
    if utc_dt is None:
        return 'Never'
    
    local_dt = utc_to_local(utc_dt)
    return local_dt.strftime(format_str)


def format_local_time(utc_dt, format_str='%H:%M:%S'):
    """Convert UTC datetime to local timezone and format time only"""
    if utc_dt is None:
        return 'No data'
    
    local_dt = utc_to_local(utc_dt)
    return local_dt.strftime(format_str)


def format_local_date(utc_dt, format_str='%Y-%m-%d'):
    """Convert UTC datetime to local timezone and format date only"""
    if utc_dt is None:
        return 'No data'
    
    local_dt = utc_to_local(utc_dt)
    return local_dt.strftime(format_str)


def format_local_datetime_full(utc_dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Convert UTC datetime to local timezone and format with full timestamp"""
    if utc_dt is None:
        return 'Never'
    
    local_dt = utc_to_local(utc_dt)
    return local_dt.strftime(format_str)