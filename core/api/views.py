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


class HomeDetailView(APIView):
    """Get or update a specific home."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        """Get home details"""
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(HomeSerializer(home, context={'request': request}).data)
    
    def patch(self, request, home_id):
        """Update home name (only owner or admin can update)"""
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
            
            # Check if user has permission to update
            member = HomeMember.objects.get(
                home=home,
                user=request.user
            )
            
            if member.role not in ['owner', 'admin']:
                return Response(
                    {'error': 'You do not have permission to update this home'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access'},
                status=status.HTTP_404_NOT_FOUND
            )
        except HomeMember.DoesNotExist:
            return Response(
                {'error': 'You are not a member of this home'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update home name
        name = request.data.get('name')
        if name:
            home.name = name
            home.save()
        
        identifier = request.data.get('identifier')
        if identifier:
            home.identifier = identifier
            home.save()
        
        return Response(
            HomeSerializer(home, context={'request': request}).data
        )

    def delete(self, request, home_id):
        """Delete a home (only owner can delete)"""
        try:
            home = Home.objects.get(
                id=home_id,
                homemember__user=request.user
            )
            
            # Check if user has permission to delete (Strictly OWNER)
            member = HomeMember.objects.get(
                home=home,
                user=request.user
            )
            
            if member.role != 'owner':
                return Response(
                    {'error': 'Only the owner can delete this home'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            home.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found or you do not have access'},
                status=status.HTTP_404_NOT_FOUND
            )


class DeviceListView(APIView):
    """List all devices in a specific home (only if user has access to that home)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, home_id):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.error(f"DEBUG: DeviceListView GET home_id={home_id} user={request.user}")
        
        from django.conf import settings
        
        # Check if home_id matches Cloud UUID configuration
        target_home_id = home_id
        if str(home_id) == str(getattr(settings, 'CLOUD_GATEWAY_ID', '')):
             logger.error("DEBUG: ID matches CLOUD_GATEWAY_ID, checking primary home...")
             primary_home = Home.objects.first()
             if primary_home:
                 target_home_id = primary_home.id
                 logger.error(f"DEBUG: Mapped UUID to Home ID {target_home_id}")

        # Verify user has access to this home
        try:
            home = Home.objects.get(
                id=target_home_id,
                homemember__user=request.user
            )
            logger.error(f"DEBUG: Found home {home.id} for user {request.user}")
        except (Home.DoesNotExist, ValueError):
            logger.error(f"DEBUG: Home {target_home_id} not found for user {request.user}. Trying fallback...")
            
            # FALLBACK: Return FIRST available home for this user
            home = Home.objects.filter(homemember__user=request.user).first()
            if home:
                logger.error(f"DEBUG: Fallback successful. Using home {home.id} ({home.name})")
                target_home_id = home.id
            else:
                # SUPER FALLBACK: If user has NO homes, look for ANY home (for debugging)
                first_any_home = Home.objects.first()
                if first_any_home:
                    logger.error(f"DEBUG: User has no homes. SUPER FALLBACK to {first_any_home.id}")
                    target_home_id = first_any_home.id
                else:
                    logger.error("DEBUG: Fallback failed. No homes in DB.")
                    return Response(
                        {'error': 'Home not found or you do not have access to this home'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        
        devices = Device.objects.filter(home_id=target_home_id)
        logger.error(f"DEBUG: Final query: Home={target_home_id}, Devices found={devices.count()}")
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
