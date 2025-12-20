from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Entity, HomeMember
from core.services.device_control import control_entity


class ControlEntityView(APIView):
    """Control an entity by sending MQTT commands (only if user has access to the entity's home)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, entity_id):
        try:
            entity = Entity.objects.select_related('device__home').get(id=entity_id)
            
            # Verify user has access to this entity's home
            if not HomeMember.objects.filter(
                home=entity.device.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to control this entity'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            value = request.data  # JSON body from Android

            # Send MQTT command via service layer
            control_entity(entity, value)

            return Response({
                "status": "command_sent",
                "entity_id": entity_id,
                "command": value
            })

        except Entity.DoesNotExist:
            return Response(
                {"error": "Entity not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
