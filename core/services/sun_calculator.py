"""
Sun Calculator Service for Astronomical Automations

Calculates sunrise, sunset, dawn, dusk, and solar noon times
for a given location using the astral library.
"""

from astral import LocationInfo
from astral.sun import sun, dawn, dusk, noon
from datetime import datetime, timedelta
import pytz


class SunCalculator:
    """Calculate sunrise, sunset, and other astronomical events."""
    
    @staticmethod
    def get_sun_times(home, date=None):
        """
        Get sun times for a specific home and date.
        
        Args:
            home: Home model instance with lat/lon/timezone
            date: datetime.date object (default: today in home's timezone)
            
        Returns:
            dict with sunrise, sunset, dawn, dusk, noon times (timezone-aware)
            
        Raises:
            ValueError: If home location is not configured
        """
        if not home.latitude or not home.longitude:
            raise ValueError(f"Home '{home.name}' location not configured. Please set latitude and longitude.")
        
        # Create location info
        location = LocationInfo(
            name=home.name,
            region="",
            timezone=home.timezone,
            latitude=float(home.latitude),
            longitude=float(home.longitude)
        )
        
        # Get timezone
        tz = pytz.timezone(home.timezone)
        
        # Use provided date or today in home's timezone
        if date is None:
            date = datetime.now(tz).date()
        
        # Calculate sun times
        s = sun(location.observer, date=date, tzinfo=tz)
        
        return {
            'sunrise': s['sunrise'],
            'sunset': s['sunset'],
            'dawn': dawn(location.observer, date=date, tzinfo=tz),
            'dusk': dusk(location.observer, date=date, tzinfo=tz),
            'noon': noon(location.observer, date=date, tzinfo=tz),
        }
    
    @staticmethod
    def get_next_sun_event(home, event_type, offset_minutes=0):
        """
        Get the next occurrence of a sun event with optional offset.
        
        Args:
            home: Home model instance
            event_type: 'sunrise', 'sunset', 'dawn', 'dusk', 'noon'
            offset_minutes: Minutes to add/subtract from event time
            
        Returns:
            datetime of next event occurrence (timezone-aware)
            
        Raises:
            ValueError: If home location not configured or invalid event type
        """
        valid_events = ['sunrise', 'sunset', 'dawn', 'dusk', 'noon']
        if event_type not in valid_events:
            raise ValueError(f"Invalid event type '{event_type}'. Must be one of: {valid_events}")
        
        tz = pytz.timezone(home.timezone)
        now = datetime.now(tz)
        
        # Try today first
        sun_times = SunCalculator.get_sun_times(home, now.date())
        event_time = sun_times[event_type]
        
        # Add offset
        if offset_minutes != 0:
            event_time += timedelta(minutes=offset_minutes)
        
        # If event already passed today, get tomorrow's
        if event_time < now:
            tomorrow = now.date() + timedelta(days=1)
            sun_times = SunCalculator.get_sun_times(home, tomorrow)
            event_time = sun_times[event_type]
            
            # Add offset again for tomorrow's event
            if offset_minutes != 0:
                event_time += timedelta(minutes=offset_minutes)
        
        return event_time
    
    @staticmethod
    def format_sun_times(sun_times):
        """
        Format sun times dictionary for API response.
        
        Args:
            sun_times: dict from get_sun_times()
            
        Returns:
            dict with ISO formatted time strings
        """
        return {
            key: value.isoformat()
            for key, value in sun_times.items()
        }
