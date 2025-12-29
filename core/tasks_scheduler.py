"""
Time and Astronomical Automation Checker

Celery Beat periodic task that runs every minute to check and execute
time-based and astronomical automations.
"""

from celery import shared_task
from datetime import datetime, time
import pytz


@shared_task
def check_time_automations():
    """
    Check and execute time-based and astronomical automations.
    
    This task runs every minute via Celery Beat and checks:
    - Time triggers: Specific time of day + day of week
    - Sun triggers: Sunrise, sunset, dawn, dusk, noon with offsets
    
    Automations that match their triggers and pass cooldown checks
    will be executed.
    """
    from core.models import Automation, AutomationTrigger
    from core.services.sun_calculator import SunCalculator
    from django.utils.timezone import now as django_now
    
    current_time = django_now()
    
    print(f"⏰ Checking time/sun automations at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get all active automations with time or sun triggers
    automations = Automation.objects.filter(
        enabled=True,
        triggers__trigger_type__in=['time', 'sun']
    ).distinct().select_related('home').prefetch_related('triggers', 'actions')
    
    executed_count = 0
    
    for automation in automations:
        try:
            should_trigger = False
            trigger_logic = automation.trigger_logic  # 'AND' or 'OR'
            
            # Evaluate all triggers
            trigger_results = []
            for trigger in automation.triggers.all():
                if trigger.trigger_type == 'time':
                    result = _check_time_trigger(trigger, current_time)
                    trigger_results.append(result)
                elif trigger.trigger_type == 'sun':
                    result = _check_sun_trigger(trigger, automation.home, current_time)
                    trigger_results.append(result)
            
            # Apply trigger logic
            if trigger_logic == 'AND':
                should_trigger = all(trigger_results) if trigger_results else False
            else:  # OR
                should_trigger = any(trigger_results) if trigger_results else False
            
            if should_trigger:
                # Check cooldown
                if _is_in_cooldown(automation):
                    print(f"  ⏳ Automation '{automation.name}' in cooldown")
                    continue
                
                # Execute automation
                print(f"  🎯 Executing automation: {automation.name}")
                _execute_automation_actions(automation)
                executed_count += 1
                
        except Exception as e:
            print(f"  ❌ Error checking automation {automation.id} '{automation.name}': {e}")
            import traceback
            traceback.print_exc()
    
    if executed_count > 0:
        print(f"✅ Executed {executed_count} automation(s)")
    
    return f"Checked automations, executed {executed_count}"


def _check_time_trigger(trigger, current_time):
    """
    Check if a time trigger should fire.
    
    Args:
        trigger: AutomationTrigger instance with trigger_type='time'
        current_time: Current datetime (timezone-aware)
        
    Returns:
        bool: True if trigger matches current time
    """
    # Convert to home timezone
    home_tz = pytz.timezone(trigger.automation.home.timezone)
    local_time = current_time.astimezone(home_tz)
    
    # Check time of day
    if trigger.time_of_day:
        trigger_time = trigger.time_of_day
        current_time_only = local_time.time()
        
        # Match within 1-minute window (since task runs every minute)
        if not (trigger_time.hour == current_time_only.hour and 
                trigger_time.minute == current_time_only.minute):
            return False
    
    # Check day of week
    if trigger.days_of_week:
        current_day = local_time.weekday()  # 0=Monday, 6=Sunday
        if current_day not in trigger.days_of_week:
            return False
    
    return True


def _check_sun_trigger(trigger, home, current_time):
    """
    Check if a sun trigger should fire.
    
    Args:
        trigger: AutomationTrigger instance with trigger_type='sun'
        home: Home instance
        current_time: Current datetime (timezone-aware)
        
    Returns:
        bool: True if sun event is happening now
    """
    if not trigger.sun_event:
        return False
    
    try:
        # Get next sun event time
        event_time = SunCalculator.get_next_sun_event(
            home,
            trigger.sun_event,
            trigger.sun_offset
        )
        
        # Check if event is within the last minute
        # (since this task runs every minute)
        time_diff = (current_time - event_time).total_seconds()
        
        # Trigger if event happened in the last 60 seconds
        return -60 < time_diff <= 0
        
    except Exception as e:
        print(f"    ❌ Error calculating sun event: {e}")
        return False


def _is_in_cooldown(automation):
    """
    Check if automation is in cooldown period.
    
    Args:
        automation: Automation instance
        
    Returns:
        bool: True if in cooldown
    """
    from core.models import AutomationExecution
    from django.utils.timezone import now as django_now
    from datetime import timedelta
    
    if automation.cooldown_seconds <= 0:
        return False
    
    # Get last execution
    last_execution = AutomationExecution.objects.filter(
        automation=automation
    ).order_by('-executed_at').first()
    
    if not last_execution:
        return False
    
    # Check if cooldown period has passed
    cooldown_end = last_execution.executed_at + timedelta(seconds=automation.cooldown_seconds)
    return django_now() < cooldown_end


def _execute_automation_actions(automation):
    """
    Execute all actions for an automation via Celery tasks.
    
    Args:
        automation: Automation instance
    """
    from core.models import AutomationExecution
    from core.tasks import control_entity, run_scene
    from django.utils.timezone import now as django_now
    
    # Record execution
    AutomationExecution.objects.create(
        automation=automation,
        executed_at=django_now()
    )
    
    # Execute each action via Celery
    for action in automation.actions.all():
        try:
            if action.entity and action.command:
                print(f"    📤 Queued entity control: {action.entity.name}: {action.command}")
                # Queue via Celery (async with retry)
                control_entity.delay(action.entity.id, action.command)
            elif action.scene:
                print(f"    🎬 Queued scene: {action.scene.name}")
                # Queue scene execution
                run_scene.delay(action.scene.id)
        except Exception as e:
            print(f"    ❌ Error queueing action: {e}")
