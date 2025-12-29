"""
Subscription views for cloud access management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.models import Home, HomeMember


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription(request, home_id):
    """Check if home has active cloud subscription."""
    home = get_object_or_404(Home, id=home_id)
    
    # Check permission
    member = HomeMember.objects.filter(home=home, user=request.user).first()
    if not member:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    # Check if user HAS subscription (not if it's currently enabled)
    has_cloud = home.cloud_subscription_tier != 'free'
    
    # Check expiry
    if has_cloud and home.cloud_expires_at:
        if home.cloud_expires_at < timezone.now():
            has_cloud = False
    
    return Response({
        'has_cloud_access': has_cloud,
        'tier': home.cloud_subscription_tier,
        'expires_at': home.cloud_expires_at.isoformat() if home.cloud_expires_at else None,
        'cloud_enabled': home.cloud_enabled
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def toggle_cloud_mode(request, home_id):
    """Enable/disable cloud mode for home."""
    home = get_object_or_404(Home, id=home_id)
    
    # Only owner can toggle
    member = HomeMember.objects.filter(home=home, user=request.user, role='owner').first()
    if not member:
        return Response(
            {'error': 'Only owner can toggle cloud mode'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    enabled = request.data.get('enabled', False)
    
    # Check subscription
    if enabled and home.cloud_subscription_tier == 'free':
        return Response({
            'error': 'Subscription required',
            'message': 'Upgrade to Basic plan for cloud access'
        }, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    home.cloud_enabled = enabled
    home.save()
    
    return Response({
        'cloud_enabled': home.cloud_enabled,
        'message': f"Cloud mode {'enabled' if enabled else 'disabled'}"
    })
