"""
Energy Monitoring API Endpoints
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from core.models import EnergyLog, Home, UserEnergySettings


class EnergyViewSet(viewsets.ViewSet):
    """Energy monitoring endpoints"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get energy consumption for a specific home"""
        home_id = request.query_params.get('home')
        
        if not home_id:
            return Response(
                {'error': 'home parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            home = Home.objects.get(id=home_id, owner=request.user)
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get today's energy data
        today = timezone.now().date()
        logs = EnergyLog.objects.filter(
            entity__device__home=home,
            date=today
        )
        
        total_kwh = logs.aggregate(Sum('estimated_kwh'))['estimated_kwh__sum'] or 0
        total_cost = logs.aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or 0
        
        # Top consumers (top 5)
        top_consumers = logs.order_by('-estimated_kwh')[:5].values(
            'entity__id',
            'entity__name',
            'estimated_kwh',
            'estimated_cost',
            'on_duration_seconds'
        )
        
        return Response({
            'today': {
                'date': today.isoformat(),
                'total_kwh': float(total_kwh),
                'total_cost': float(total_cost) if total_cost else 0,
                'top_consumers': list(top_consumers)
            }
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get energy history for last N days"""
        home_id = request.query_params.get('home')
        days = int(request.query_params.get('days', 7))
        
        if not home_id:
            return Response(
                {'error': 'home parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            home = Home.objects.get(id=home_id, owner=request.user)
        except Home.DoesNotExist:
            return Response(
                {'error': 'Home not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        start_date = timezone.now().date() - timedelta(days=days-1)
        
        logs = EnergyLog.objects.filter(
            entity__device__home=home,
            date__gte=start_date
        ).values('date').annotate(
            total_kwh=Sum('estimated_kwh'),
            total_cost=Sum('estimated_cost')
        ).order_by('date')
        
        # Format response
        history_data = []
        for log in logs:
            history_data.append({
                'date': log['date'].isoformat(),
                'kwh': float(log['total_kwh'] or 0),
                'cost': float(log['total_cost'] or 0)
            })
        
        return Response({
            'start_date': start_date.isoformat(),
            'end_date': timezone.now().date().isoformat(),
            'days': days,
            'history': history_data
        })
    
    @action(detail=False, methods=['get', 'put'], url_path='settings')
    def user_settings(self, request):
        """Get or update user energy settings"""
        if request.method == 'GET':
            settings, created = UserEnergySettings.objects.get_or_create(
                user=request.user
            )
            return Response({
                'electricity_rate': float(settings.electricity_rate_per_kwh),
                'currency': settings.currency
            })
        
        elif request.method == 'PUT':
            settings, created = UserEnergySettings.objects.get_or_create(
                user=request.user
            )
            
            if 'electricity_rate' in request.data:
                settings.electricity_rate_per_kwh = request.data['electricity_rate']
            if 'currency' in request.data:
                settings.currency = request.data['currency']
            
            settings.save()
            
            return Response({
                'electricity_rate': float(settings.electricity_rate_per_kwh),
                'currency': settings.currency,
                'message': 'Settings updated successfully'
            })
