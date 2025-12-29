"""
API endpoints for home location and sun time calculations.

These endpoints support time-based and astronomical automations.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Home, HomeMember


class HomeLocationView(APIView):
    """Update home location for astronomical calculations."""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, home_id):
        """
        Update home location (latitude, longitude, timezone, elevation).
        
        Required for sunrise/sunset automation triggers.
        """
        try:
            # Verify user has access to this home
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update location fields
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        timezone = request.data.get('timezone', 'UTC')
        elevation = request.data.get('elevation', 0)
        
        if latitude is not None:
            home.latitude = latitude
        if longitude is not None:
            home.longitude = longitude
        if timezone:
            home.timezone = timezone
        if elevation is not None:
            home.elevation = elevation
        
        home.save()
        
        return Response({
            'status': 'success',
            'message': 'Home location updated successfully',
            'location': {
                'latitude': float(home.latitude) if home.latitude else None,
                'longitude': float(home.longitude) if home.longitude else None,
                'timezone': home.timezone,
                'elevation': home.elevation
            }
        })


class SunTimesView(APIView):
    """Get today's sun times for a home."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        """
        Calculate and return sun times (sunrise, sunset, dawn, dusk, noon)
        for the home's location and timezone.
        """
        try:
            # Verify user has access to this home
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if location is configured
        if not home.latitude or not home.longitude:
            return Response(
                {
                    'error': 'Home location not configured',
                    'message': 'Please set latitude and longitude for this home to calculate sun times'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.services.sun_calculator import SunCalculator
            
            # Get sun times for today
            sun_times = SunCalculator.get_sun_times(home)
            
            # Format for API response
            formatted_times = SunCalculator.format_sun_times(sun_times)
            
            return Response({
                'home_id': home_id,
                'home_name': home.name,
                'location': {
                    'latitude': float(home.latitude),
                    'longitude': float(home.longitude),
                    'timezone': home.timezone,
                    'elevation': home.elevation
                },
                'sun_times': formatted_times
            })
            
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to calculate sun times',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
