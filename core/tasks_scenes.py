"""
Celery tasks for scene execution with retry logic.
"""

from celery import shared_task
import json


@shared_task(bind=True, max_retries=3)
def run_scene(self, scene_id):
    """
    Execute scene actions asynchronously.
    
    Args:
        scene_id: Scene ID to execute
        
    Returns:
        dict: Execution result
    """
    try:
        from core.models import Scene
        
        scene = Scene.objects.prefetch_related('actions', 'actions__entity').get(id=scene_id)
        
        print(f"🎬 Executing scene: {scene.name}")
        
        # Queue each action
        for action in scene.actions.all():
            if action.entity and action.command:
                # Import here to avoid circular dependency
                from core.tasks import control_entity
                control_entity.delay(action.entity.id, action.command)
        
        return {'status': 'success', 'scene_id': scene_id, 'scene_name': scene.name}
        
    except Exception as e:
        print(f"❌ Scene execution failed: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
