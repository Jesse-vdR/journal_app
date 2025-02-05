from datetime import datetime

def datetime_filter(value):
    """Format a datetime object."""
    if value is None:
        return ''
    return value.strftime('%Y-%m-%d %H:%M:%S')
