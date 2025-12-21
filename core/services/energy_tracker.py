"""
Energy Tracking Service
Tracks device power consumption and calculates energy costs
"""

from datetime import datetime
from django.utils import timezone
from core.models import Entity, EnergyLog, UserEnergySettings


class EnergyTracker:
    """Service to track and calculate energy consumption"""
    
    @staticmethod
    def track_state_change(entity, old_state, new_state):
        """
        Called when entity state changes.
        If device turns off, calculate energy consumed since it was turned on.
        """
        # Only track power-consuming devices
        if entity.entity_type not in ['light', 'fan', 'switch']:
            return
        
        # Extract power state from state JSON
        old_power = old_state.get('power') if isinstance(old_state, dict) else None
        new_power = new_state.get('power') if isinstance(new_state, dict) else None
        
        # Device turned off - calculate energy
        if old_power is True and new_power is False:
            EnergyTracker._calculate_and_log_energy(entity)
    
    @staticmethod
    def _calculate_and_log_energy(entity):
        """Calculate energy consumption and update/create log"""
        # Find the last time the device was turned on
        from core.models import StateHistory
        
        last_on_state = StateHistory.objects.filter(
            entity=entity,
            state__power=True,
            timestamp__lt=timezone.now()
        ).order_by('-timestamp').first()
        
        if not last_on_state:
            return  # No previous ON state found
        
        # Calculate duration
        duration_seconds = (timezone.now() - last_on_state.timestamp).total_seconds()
        
        # Calculate energy consumption
        kwh = EnergyLog.calculate_energy(entity, duration_seconds)
        
        # Get today's date
        today = timezone.now().date()
        
        # Update or create log for today
        log, created = EnergyLog.objects.get_or_create(
            entity=entity,
            date=today,
            defaults={
                'on_duration_seconds': 0,
                'estimated_kwh': 0
            }
        )
        
        # Add to today's total
        log.on_duration_seconds += int(duration_seconds)
        log.estimated_kwh += kwh
        
        # Calculate cost
        try:
            settings = entity.device.home.user.energy_settings
            log.estimated_cost = log.estimated_kwh * settings.electricity_rate_per_kwh
        except UserEnergySettings.DoesNotExist:
            # Create default settings
            settings, _ = UserEnergySettings.objects.get_or_create(
                user=entity.device.home.user
            )
            log.estimated_cost = log.estimated_kwh * settings.electricity_rate_per_kwh
        
        log.save()
        
        print(f"⚡ ENERGY: {entity.name} consumed {kwh:.4f} kWh (₹{log.estimated_cost:.2f})")
