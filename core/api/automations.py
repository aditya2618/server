from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Automation, AutomationTrigger, AutomationAction, Home, HomeMember
from core.api.serializers import AutomationSerializer


class AutomationListView(APIView):
    """List all automations in a home or create a new automation."""
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
        
        automations = Automation.objects.filter(home_id=home_id).prefetch_related(
            'triggers__entity',
            'actions__entity',
            'actions__scene'
        )
        return Response(AutomationSerializer(automations, many=True).data)
    
    def post(self, request, home_id):
        """Create a new automation"""
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
        
        # Add home_id to request data
        data = request.data.copy()
        data['home'] = home_id
        
        serializer = AutomationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AutomationDetailView(APIView):
    """Get, update, or delete a specific automation."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, automation_id):
        try:
            automation = Automation.objects.select_related('home').prefetch_related(
                'triggers__entity',
                'actions__entity',
                'actions__scene'
            ).get(id=automation_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=automation.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this automation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return Response(AutomationSerializer(automation).data)
            
        except Automation.DoesNotExist:
            return Response(
                {"error": "Automation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, automation_id):
        """Update an existing automation"""
        try:
            automation = Automation.objects.select_related('home').get(id=automation_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=automation.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this automation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = AutomationSerializer(automation, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Automation.DoesNotExist:
            return Response(
                {"error": "Automation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, automation_id):
        """Delete an automation"""
        try:
            automation = Automation.objects.select_related('home').get(id=automation_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=automation.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this automation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            automation.delete()
            # 204 NO_CONTENT should not have a response body
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Automation.DoesNotExist:
            return Response(
                {"error": "Automation not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class AutomationToggleView(APIView):
    """Toggle automation enabled/disabled status."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, automation_id):
        try:
            automation = Automation.objects.select_related('home').get(id=automation_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=automation.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this automation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Toggle enabled status
            automation.enabled = not automation.enabled
            automation.save(update_fields=['enabled'])
            
            return Response({
                'status': 'success',
                'automation_id': automation_id,
                'enabled': automation.enabled
            })
            
        except Automation.DoesNotExist:
            return Response(
                {"error": "Automation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
