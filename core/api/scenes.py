from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Scene, SceneAction, Home, HomeMember
from core.api.serializers import SceneSerializer
from core.tasks import run_scene


class SceneListView(APIView):
    """List all scenes in a home (only if user has access to that home)."""
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
        
        # Filter scenes created by this user only (private scenes)
        scenes = Scene.objects.filter(
            home_id=home_id,
            created_by=request.user
        ).prefetch_related('actions__entity')
        return Response(SceneSerializer(scenes, many=True).data)
    
    def post(self, request, home_id):
        """Create a new scene"""
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
        
        serializer = SceneSerializer(data=data)
        if serializer.is_valid():
            # Set created_by to current user
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SceneDetailView(APIView):
    """Get, update, or delete a specific scene."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, scene_id):
        try:
            scene = Scene.objects.select_related('home').prefetch_related(
                'actions__entity'
            ).get(id=scene_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=scene.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this scene'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return Response(SceneSerializer(scene).data)
            
        except Scene.DoesNotExist:
            return Response(
                {"error": "Scene not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, scene_id):
        """Update an existing scene"""
        try:
            scene = Scene.objects.select_related('home').get(id=scene_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=scene.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this scene'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = SceneSerializer(scene, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Scene.DoesNotExist:
            return Response(
                {"error": "Scene not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, scene_id):
        """Delete a scene"""
        try:
            scene = Scene.objects.select_related('home').get(id=scene_id)
            
            # Verify user has access
            if not HomeMember.objects.filter(
                home=scene.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this scene'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            scene.delete()
            return Response(
                {'message': 'Scene deleted successfully'},
                status=status.HTTP_200_OK
            )
            
        except Scene.DoesNotExist:
            return Response(
                {"error": "Scene not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class RunSceneView(APIView):
    """Trigger scene execution asynchronously (only if user has access to the scene's home)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, scene_id):
        try:
            scene = Scene.objects.select_related('home').get(id=scene_id)
            
            # Verify user has access to this scene's home
            if not HomeMember.objects.filter(
                home=scene.home,
                user=request.user
            ).exists():
                return Response(
                    {'error': 'You do not have access to this scene'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            
            # Execute scene directly (synchronous)
            # Previously used Celery which requires a worker
            try:
                from core.models import SceneAction
                from core.tasks import control_entity
                
                actions = SceneAction.objects.filter(scene_id=scene.id).order_by("order")
                
                print(f"🎬 Running scene '{scene.name}' (ID={scene.id}) with {actions.count()} action(s)")
                
                for action in actions:
                    print(f"  → Action #{action.order}: {action.entity.name} = {action.value}")
                    control_entity(action.entity, action.value)
                
                return Response({
                    "status": "scene_executed",
                    "scene_id": scene_id,
                    "scene_name": scene.name,
                    "actions_count": actions.count()
                })
            except Exception as e:
                print(f"❌ Error running scene: {e}")
                import traceback
                traceback.print_exc()
                return Response(
                    {"error": f"Failed to execute scene: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            

        except Scene.DoesNotExist:
            return Response(
                {"error": "Scene not found"},
                status=status.HTTP_404_NOT_FOUND
            )
