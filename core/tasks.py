from celery import shared_task
from core.models import Automation, AutomationTrigger, AutomationAction
import json


def control_entity(entity, command):
    """
    Publish MQTT command to control an entity.
    
    Args:
        entity: Entity model instance
        command: Dict with command payload (e.g., {"power": true, "brightness": 80})
    """
    from core.mqtt.client import mqtt_client
    
    try:
        topic = entity.command_topic()
        payload = json.dumps(command)
        
        # Publish to MQTT
        mqtt_client.publish(topic, payload)
        print(f"📤 Published: {topic} -> {payload}")
        
        # Update entity state optimistically
        entity.state.update(command)
        entity.save(update_fields=['state'])
        
    except Exception as e:
        print(f"❌ Error controlling entity {entity.name}: {e}")


@shared_task
def evaluate_automations(entity_id):
    """
    Called whenever an entity state changes.
    
    Evaluates all automation triggers for this entity and executes actions if conditions are met.
    """
    triggers = AutomationTrigger.objects.filter(entity_id=entity_id)

    for trigger in triggers:
        automation = trigger.automation
        if not automation.enabled:
            continue

        entity = trigger.entity
        state = entity.state

        # Determine value to compare
        attribute = trigger.attribute or "value"
        current_value = state.get(attribute)

        if current_value is None:
            continue

        # Try to convert to numeric for comparison
        try:
            current_value = float(current_value)
            trigger_value = float(trigger.value)
        except (ValueError, TypeError):
            # Fall back to string comparison for "=="
            current_value = str(current_value)
            trigger_value = trigger.value

        # Evaluate condition
        triggered = False
        
        if trigger.operator == ">":
            try:
                triggered = float(current_value) > float(trigger_value)
            except (ValueError, TypeError):
                pass
                
        elif trigger.operator == "<":
            try:
                triggered = float(current_value) < float(trigger_value)
            except (ValueError, TypeError):
                pass
                
        elif trigger.operator == "==":
            triggered = str(current_value) == str(trigger_value)

        if triggered:
            print(f"🤖 Automation triggered: {automation.name}")
            run_actions(automation)


def run_actions(automation):
    """
    Execute all actions for an automation.
    """
    actions = AutomationAction.objects.filter(automation=automation)

    for action in actions:
        if action.scene:
            # Trigger scene execution
            run_scene.delay(action.scene.id)
            print(f"  → Triggering scene: {action.scene.name}")
        elif action.entity:
            # Direct entity control
            print(f"  → Executing action on {action.entity.name}: {action.command}")
            control_entity(action.entity, action.command)


@shared_task
def run_scene(scene_id):
    """
    Execute a scene by running all its actions in order.
    
    Args:
        scene_id: ID of the scene to execute
    """
    from core.models import SceneAction
    
    actions = SceneAction.objects.filter(scene_id=scene_id).order_by("order")
    
    print(f"🎬 Running scene (ID={scene_id}) with {actions.count()} action(s)")
    
    for action in actions:
        print(f"  → Action #{action.order}: {action.entity.name} = {action.value}")
        control_entity(action.entity, action.value)


@shared_task
def run_schedule(schedule_id):
    """
    Execute a scheduled task (scene, automation, or entity control).
    
    Called by Celery Beat at scheduled times.
    
    Args:
        schedule_id: ID of the schedule to execute
    """
    from core.models import Schedule
    
    try:
        schedule = Schedule.objects.get(id=schedule_id, enabled=True)
    except Schedule.DoesNotExist:
        print(f"⏰ Schedule {schedule_id} not found or disabled")
        return
    
    print(f"⏰ Executing schedule: {schedule.name} ({schedule.schedule_type})")
    
    if schedule.schedule_type == "scene" and schedule.scene:
        print(f"  → Triggering scene: {schedule.scene.name}")
        run_scene.delay(schedule.scene.id)
    
    elif schedule.schedule_type == "entity" and schedule.entity:
        print(f"  → Controlling entity: {schedule.entity.name}")
        control_entity(schedule.entity, schedule.command)
    
    elif schedule.schedule_type == "automation" and schedule.automation:
        print(f"  → Enabling automation: {schedule.automation.name}")
        schedule.automation.enabled = True
        schedule.automation.save(update_fields=["enabled"])


@shared_task
def cleanup_old_history(days=30):
    """
    Clean up old entity state history records.
    
    This task should be scheduled to run daily via django-celery-beat
    to prevent the EntityStateHistory table from growing indefinitely.
    
    Args:
        days: Delete records older than this many days (default: 30)
    
    Returns:
        str: Summary of deletion
    """
    from django.utils.timezone import now
    from datetime import timedelta
    from core.models import EntityStateHistory
    
    cutoff_date = now() - timedelta(days=days)
    
    # Delete old records
    deleted_count, _ = EntityStateHistory.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()
    
    print(f"🗑️ Cleaned up {deleted_count} history records older than {days} days")
    
    return f"Deleted {deleted_count} old history records"
