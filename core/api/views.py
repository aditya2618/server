from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Home, Device, Entity, HomeMember
from core.api.serializers import (
    HomeSerializer,
    DeviceSerializer,
    EntitySerializer,
)


class HomeListView(APIView):
    """List all homes for the authenticated user or create a new home."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        homes = Home.objects.filter(
            homemember__user=request.user
        ).distinct()
        return Response(HomeSerializer(homes, many=True, context={'request': request}).data)
    
    def post(self, request):
        """Create a new home"""
        name = request.data.get('name')
        
        if not name:
            return Response(
                {'error': 'Home name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create home with current user as owner
        home = Home.objects.create(
            name=name,
            owner=request.user
        )
        
        # Add creator as owner member
        HomeMember.objects.create(
            home=home,
            user=request.user,
            role='owner'
        )
        
        return Response(
            HomeSerializer(home, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class DeviceListView(APIView):
    """List all devices in a specific home (only if user has access to that home)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, home_id):
        # Verify user has access to this home
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access to this home'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        devices = Device.objects.filter(home_id=home_id)
        return Response(DeviceSerializer(devices, many=True).data)


class AvailableDevicesView(APIView):
    """List all devices available to add to a home (auto-discovered but unassigned)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, home_id):
        # Verify user has access to this home
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access to this home'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get devices that are either unassigned or not in this home
        available_devices = Device.objects.filter(
            home__isnull=True
        ) | Device.objects.exclude(home_id=home_id)
        
        return Response(DeviceSerializer(available_devices, many=True).data)


class LinkDevicesView(APIView):
    """Link multiple devices to a home."""
    permission_classes = [IsAuthenticated]

    def post(self, request, home_id):
        # Verify user has access to this home
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access to this home'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        device_ids = request.data.get('device_ids', [])
        
        if not device_ids:
            return Response(
                {'error': 'device_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Link devices to home
        updated_count = Device.objects.filter(
            id__in=device_ids
        ).update(home=home)
        
        return Response({
            'status': 'success',
            'linked_count': updated_count,
            'message': f'{updated_count} device(s) added to {home.name}'
        })


class UnlinkDevicesView(APIView):
    """Unlink devices from a home."""
    permission_classes = [IsAuthenticated]

    def post(self, request, home_id):
        # Verify user has access to this home
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access to this home'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        device_ids = request.data.get('device_ids', [])
        
        if not device_ids:
            return Response(
                {'error': 'device_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Unlink devices from this home (set home to null)
        updated_count = Device.objects.filter(
            id__in=device_ids,
            home_id=home_id
        ).update(home=None)
        
        return Response({
            'status': 'success',
            'unlinked_count': updated_count,
            'message': f'{updated_count} device(s) removed from {home.name}'
        })


class EntityListView(APIView):
    """List all entities for a specific device (only if user has access to the device's home)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        # Get device and verify user has access to its home
        try:
            device = Device.objects.select_related('home').get(id=device_id)
            
            # Check if user is a member of the device's home
            if not HomeMember.objects.filter(
                home=device.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this device'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
        except Device.DoesNotExist:
            return Response(
                {'error': 'Device not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        entities = Entity.objects.filter(device_id=device_id)
        return Response(EntitySerializer(entities, many=True).data)
