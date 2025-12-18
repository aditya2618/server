from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from core.models import Scene
from core.api.serializers import SceneSerializer
from core.tasks import run_scene


class SceneListView(APIView):
    """List all scenes in a home."""
    permission_classes = [IsAuthenticated]

    def get(self, request, home_id):
        scenes = Scene.objects.filter(home_id=home_id)
        return Response(SceneSerializer(scenes, many=True).data)


class RunSceneView(APIView):
    """Trigger scene execution asynchronously."""
    permission_classes = [IsAuthenticated]

    def post(self, request, scene_id):
        try:
            scene = Scene.objects.get(id=scene_id)
            
            # Execute scene asynchronously via Celery
            run_scene.delay(scene.id)
            
            return Response({
                "status": "scene_started",
                "scene_id": scene_id,
                "scene_name": scene.name
            })
            
        except Scene.DoesNotExist:
            return Response(
                {"error": "Scene not found"},
                status=status.HTTP_404_NOT_FOUND
            )
