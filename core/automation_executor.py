"""
Production-ready automation execution engine.

Handles trigger evaluation, action execution, cooldown management,
rate limiting, and comprehensive error handling.
"""
import logging
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from core.models import Automation, AutomationTrigger, AutomationAction, Entity, Scene
from core.mqtt.client import publish_command
import json

logger = logging.getLogger('automations')

# Configuration
MAX_EXECUTIONS_PER_MINUTE = 10
DEFAULT_COOLDOWN_SECONDS = 60


class AutomationExecutor:
    """Main automation execution service"""
    
    @staticmethod
    def evaluate_trigger(trigger: AutomationTrigger, value: Any) -> bool:
        """
        Evaluate if a trigger condition is met.
        
        Args:
            trigger: AutomationTrigger instance
            value: Current entity value to check
            
        Returns:
            bool: True if condition matches, False otherwise
        """
        try:
            if trigger.operator == '>':
                return float(value) > float(trigger.value)
            elif trigger.operator == '<':
                return float(value) < float(trigger.value)
            elif trigger.operator == '==':
                return str(value) == str(trigger.value)
            else:
                logger.warning(f"Unknown operator: {trigger.operator}")
                return False
        except (ValueError, TypeError) as e:
            logger.error(f"Error evaluating trigger {trigger.id}: {e}")
            return False
    
    @staticmethod
    def check_execution_limit(automation_id: int) -> bool:
        """
        Check if automation has hit rate limit.
        
        Args:
            automation_id: Automation ID to check
            
        Returns:
            bool: True if can execute, False if rate limited
        """
        key = f"automation_executions_{automation_id}"
        count = cache.get(key, 0)
        
        if count >= MAX_EXECUTIONS_PER_MINUTE:
            logger.warning(
                f"⚠️  Automation {automation_id} hit rate limit "
                f"({count}/{MAX_EXECUTIONS_PER_MINUTE} executions/minute)"
            )
            return False
        
        cache.set(key, count + 1, timeout=60)
        return True
    
    @staticmethod
    def should_execute_automation(automation_id: int, cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS) -> bool:
        """
        Check if automation is in cooldown period.
        
        Args:
            automation_id: Automation ID to check
            cooldown_seconds: Cooldown period in seconds
            
        Returns:
            bool: True if can execute, False if in cooldown
        """
        cooldown_key = f"automation_cooldown_{automation_id}"
        
        if cache.get(cooldown_key):
            logger.debug(f"Automation {automation_id} still in cooldown")
            return False
        
        cache.set(cooldown_key, True, timeout=cooldown_seconds)
        return True
    
    @staticmethod
    def execute_device_action(action: AutomationAction) -> bool:
        """
        Execute a device control action.
        
        Args:
            action: AutomationAction instance with entity
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            entity = action.entity
            
            # Use the helper method from Entity model to get correct topic
            topic = entity.command_topic()
            
            # Build command payload
            # If payload is complex (has attributes), send as is
            # If it has specific formatting requirements, client.py handles it
            payload = action.command
            
            print(f"  📤 EXECUTOR: Sending command to {entity.name} (topic={topic}): {payload}")
            
            # Publish MQTT command
            publish_command(topic, payload)
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to execute device action: {e}")
            return False
    
    @staticmethod
    def execute_scene_action(action: AutomationAction) -> bool:
        """
        Execute a scene action.
        
        Args:
            action: AutomationAction instance with scene
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from core.api.scenes import execute_scene_logic
            
            scene = action.scene
            logger.info(f"  🎬 Executing scene: {scene.name}")
            
            # Execute scene
            success, message = execute_scene_logic(scene)
            
            if success:
                logger.info(f"    ✓ Scene executed successfully")
                return True
            else:
                logger.warning(f"    ⚠️  Scene execution issues: {message}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Failed to execute scene action: {e}")
            return False
    
    @classmethod
    def execute_automation(cls, automation: Automation, trigger_entity_id: int, trigger_value: Any) -> bool:
        """
        Execute all actions in an automation with error handling.
        
        Args:
            automation: Automation instance to execute
            trigger_entity_id: Entity ID that triggered this automation
            trigger_value: Value that triggered the automation
            
        Returns:
            bool: True if all actions succeeded, False if any failed
        """
        logger.info(f"🤖 [START] Executing automation: {automation.name}")
        
        all_success = True
        
        try:
            actions = automation.actions.select_related('entity', 'scene').all()
            
            for i, action in enumerate(actions, 1):
                try:
                    action_desc = cls._get_action_description(action)
                    logger.info(f"  ↳ Action {i}/{len(actions)}: {action_desc}")
                    
                    if action.entity:
                        success = cls.execute_device_action(action)
                    elif action.scene:
                        success = cls.execute_scene_action(action)
                    else:
                        logger.warning(f"  ⚠️  Action {i} has no entity or scene")
                        success = False
                    
                    if not success:
                        all_success = False
                        
                except Exception as e:
                    logger.error(f"  ❌ Action {i} failed: {e}")
                    all_success = False
                    # Continue with remaining actions
            
            status = "✅ [DONE]" if all_success else "⚠️  [DONE WITH ERRORS]"
            logger.info(f"{status} {automation.name}")
            
            # Record execution
            cls._record_execution(automation, trigger_entity_id, trigger_value, all_success)
            
            return all_success
            
        except Exception as e:
            logger.error(f"❌ [FAILED] Automation {automation.name}: {e}")
            cls._record_execution(automation, trigger_entity_id, trigger_value, False, str(e))
            return False
    
    @staticmethod
    def _get_action_description(action: AutomationAction) -> str:
        """Get human-readable action description"""
        if action.entity:
            cmd_parts = []
            if action.command.get('power') is not None:
                cmd_parts.append('ON' if action.command['power'] else 'OFF')
            if action.command.get('brightness'):
                cmd_parts.append(f"{action.command['brightness']}%")
            if action.command.get('speed'):
                cmd_parts.append(f"speed {action.command['speed']}")
            
            cmd_str = ' '.join(cmd_parts) if cmd_parts else str(action.command)
            return f"Control {action.entity.name} → {cmd_str}"
        elif action.scene:
            return f"Run scene: {action.scene.name}"
        else:
            return "Unknown action"
    
    @staticmethod
    def _record_execution(automation: Automation, trigger_entity_id: int, 
                         trigger_value: Any, success: bool, error_message: str = "") -> None:
        """Record automation execution for monitoring"""
        try:
            from core.models import AutomationExecution
            
            AutomationExecution.objects.create(
                automation=automation,
                trigger_entity_id=trigger_entity_id,
                trigger_value=str(trigger_value),
                success=success,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to record execution: {e}")
    
    @classmethod
    @transaction.atomic
    def check_automations_for_entity(cls, entity_id: int, attribute: str, new_value: Any) -> None:
        """
        Check and execute automations triggered by entity state change.
        
        This is the main entry point called from MQTT handlers.
        
        Args:
            entity_id: Entity ID that changed
            attribute: Attribute that changed (e.g., 'temperature', 'state')
            new_value: New value of the attribute
        """
    @classmethod
    def check_automations_for_entity(cls, entity_id: int, attribute: str, new_value: Any) -> None:
        """
        Check and execute automations triggered by entity state change.
        """
        try:
            print(f"🔍 EXECUTOR: Checking automations for entity {entity_id}, {attribute}={new_value}")
            
            # Find enabled automations with triggers on this entity/attribute
            automations = Automation.objects.filter(
                enabled=True,
                triggers__entity_id=entity_id,
                triggers__attribute=attribute
            ).select_related('home').prefetch_related(
                'triggers',
                'actions',
                'actions__entity__device',
                'actions__scene'
            ).distinct()
            
            if not automations.exists():
                print(f"  ℹ️  EXECUTOR: No automations found for entity {entity_id} attribute '{attribute}'")
                # Debug: print what IS in the DB for this entity
                all_triggers = AutomationTrigger.objects.filter(entity_id=entity_id)
                if all_triggers.exists():
                    print(f"  ℹ️  Debug: Found triggers for entity {entity_id} but maybe attribute mismatch?")
                    for t in all_triggers:
                        print(f"    - Trigger in DB: id={t.id}, attr='{t.attribute}', auto_enabled={t.automation.enabled}")
                return
            
            print(
                f"📋 EXECUTOR: Found {automations.count()} automation(s) for "
                f"entity {entity_id} attribute '{attribute}' = {new_value}"
            )
            
            for automation in automations:
                try:
                    print(f"  🔎 EXECUTOR: Checking automation: {automation.name} (ID: {automation.id})")
                    
                    # Check all triggers for this automation
                    triggers_match = cls._check_all_triggers(automation, entity_id, attribute, new_value)
                    
                    if not triggers_match:
                        print(f"    ❌ Triggers don't match for: {automation.name}")
                        continue
                    
                    print(f"    ✓ All triggers match!")
                    
                    # Check rate limit
                    if not cls.check_execution_limit(automation.id):
                        print(f"    ⚠️  Rate limited: {automation.name}")
                        continue
                    
                    # Check cooldown
                    if not cls.should_execute_automation(automation.id):
                        print(f"    ⏳ In cooldown: {automation.name}")
                        continue
                    
                    # Execute automation
                    print(
                        f"🎯 EXECUTOR: Automation triggered: {automation.name} "
                        f"(entity {entity_id}, {attribute} = {new_value})"
                    )
                    cls.execute_automation(automation, entity_id, new_value)
                    
                except Exception as e:
                    print(f"❌ EXECUTOR: Error processing automation {automation.id}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                    
        except Exception as e:
            print(f"❌ EXECUTOR: Error in check_automations_for_entity: {e}")
            import traceback
            traceback.print_exc()
    
    @classmethod
    def _check_all_triggers(cls, automation: Automation, entity_id: int, 
                           attribute: str, new_value: Any) -> bool:
        """
        Check if ALL triggers match (AND logic).
        
        For now, we implement AND logic - all triggers must match.
        Future: Could add OR logic or more complex conditions.
        
        Args:
            automation: Automation to check
            entity_id: Entity that changed
            attribute: Attribute that changed
            new_value: New value
            
        Returns:
            bool: True if all triggers match
        """
        triggers = automation.triggers.all()
        
        for trigger in triggers:
            # For the entity that changed, use new_value
            if trigger.entity_id == entity_id and trigger.attribute == attribute:
                if not cls.evaluate_trigger(trigger, new_value):
                    return False
            else:
                # For other triggers, get current value from database
                try:
                    entity = Entity.objects.get(id=trigger.entity_id)
                    current_value = entity.current_state.get('value') if entity.current_state else None
                    
                    if current_value is None:
                        logger.warning(f"No current state for entity {trigger.entity_id}")
                        return False
                    
                    if not cls.evaluate_trigger(trigger, current_value):
                        return False
                        
                except Entity.DoesNotExist:
                    logger.error(f"Entity {trigger.entity_id} not found")
                    return False
        
        return True


# Convenience function for external use
def check_automations_for_entity(entity_id: int, attribute: str, new_value: Any) -> None:
    """
    Main entry point for checking automations.
    
    Call this from MQTT handlers when entity state changes.
    """
    AutomationExecutor.check_automations_for_entity(entity_id, attribute, new_value)
