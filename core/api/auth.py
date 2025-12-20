from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    API endpoint for mobile app login
    POST /api/auth/login/
    {
        "username": "your_username",
        "password": "your_password"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    
    return Response({'error': 'Invalid credentials'}, status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    API endpoint for user registration
    POST /api/auth/register/
    {
        "username": "your_username",
        "email": "your_email@example.com",
        "password": "your_password"
    }
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    # Validate required fields
    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=400)
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)
    
    # Check if email already exists (if provided)
    if email and User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=400)
    
    try:
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email if email else '',
            password=password
        )
        
        # Create token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=201)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    API endpoint for getting and updating user profile
    GET /api/auth/profile/ - Get current user profile
    PUT /api/auth/profile/ - Update current user profile
    {
        "email": "new_email@example.com",
        "first_name": "First",
        "last_name": "Last"
    }
    Note: Username cannot be changed
    """
    user = request.user
    
    if request.method == 'GET':
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
    
    elif request.method == 'PUT':
        # Update user profile
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Check if email is already taken by another user
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({'error': 'Email already in use'}, status=400)
            user.email = email
        
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    API endpoint for changing user password
    POST /api/auth/change-password/
    {
        "current_password": "old_password",
        "new_password": "new_password"
    }
    """
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({'error': 'Current password and new password are required'}, status=400)
    
    # Verify current password
    if not user.check_password(current_password):
        return Response({'error': 'Current password is incorrect'}, status=400)
    
    # Validate new password (you can add more validation here)
    if len(new_password) < 6:
        return Response({'error': 'New password must be at least 6 characters'}, status=400)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'})


@api_view(['POST'])
def logout_view(request):
    """
    API endpoint for mobile app logout
    POST /api/auth/logout/
    """
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    return Response({'message': 'Logged out successfully'})
