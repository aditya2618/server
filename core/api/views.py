from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Home, Device, Entity
from core.api.serializers import (
    HomeSerializer,
    DeviceSerializer,
    EntitySerializer,
)


class HomeListView(APIView):
    """List all homes for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        homes = Home.objects.filter(
            homemember__user=request.user
        ).distinct()
        return Response(HomeSerializer(homes, many=True, context={'request': request}).data)


class DeviceListView(APIView):
    """List all devices in a specific home."""
    permission_classes = [IsAuthenticated]

    def get(self, request, home_id):
        devices = Device.objects.filter(home_id=home_id)
        return Response(DeviceSerializer(devices, many=True).data)


class EntityListView(APIView):
    """List all entities for a specific device."""
    permission_classes = [IsAuthenticated]

    def get(self, request, device_id):
        entities = Entity.objects.filter(device_id=device_id)
        return Response(EntitySerializer(entities, many=True).data)
