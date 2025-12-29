from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


# 1. Home, User, Membership
class Home(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_homes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Location for astronomical calculations (sunrise/sunset)
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Latitude for sun calculations"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Longitude for sun calculations"
    )
    timezone = models.CharField(
        max_length=50, 
        default='UTC',
        help_text="Timezone (e.g., 'Asia/Kolkata', 'America/New_York')"
    )
    elevation = models.IntegerField(
        default=0,
        help_text="Elevation in meters for accurate sun calculations"
    )
    
    # Cloud subscription
    cloud_enabled = models.BooleanField(
        default=False,
        help_text="Whether cloud mode is enabled for this home"
    )
    cloud_subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free - Local Only'),
            ('basic', 'Basic - Cloud Access'),
        ],
        default='free',
        help_text="Subscription tier for cloud access"
    )
    cloud_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the cloud subscription expires"
    )

    def __str__(self):
        return self.name


class HomeMember(models.Model):
    ROLE_CHOICES = (
        ("owner", "Owner"),
        ("family", "Family"),
        ("guest", "Guest"),
    )

    home = models.ForeignKey(Home, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ("home", "user")


# 2. Room / Zone / Field (Location)
class Location(models.Model):
    LOCATION_TYPES = (
        ("room", "Room"),
        ("zone", "Zone"),
        ("field", "Field"),
        ("greenhouse", "Greenhouse"),
    )

    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)

    def __str__(self):
        return f"{self.home.name} - {self.name}"


# 3. Device (ESP32 Node)
class Device(models.Model):
    home = models.ForeignKey(
        Home, on_delete=models.CASCADE, related_name="devices",
        null=True, blank=True,
        help_text="Optional link to Home object for backward compatibility"
    )
    home_identifier = models.CharField(
        max_length=100,
        help_text="String identifier for the home (e.g., 'home_test_1', '1')"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True
    )

    name = models.CharField(max_length=100)
    node_name = models.CharField(
        max_length=100,
        help_text="Must match ESPHome node name"
    )

    firmware_version = models.CharField(max_length=50, blank=True)

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(
        default=dict, blank=True,
        help_text="Board type, mac, ip, etc"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('home_identifier', 'node_name')]

    def base_topic(self):
        return f"home/{self.home_identifier}/{self.node_name}"

    def __str__(self):
        return self.name


# 4. Entity (CORE MODEL)
class Entity(models.Model):
    ENTITY_TYPES = (
        ("sensor", "Sensor"),
        ("switch", "Switch"),
        ("relay", "Relay"),
        ("light", "Light"),
        ("fan", "Fan"),
        ("valve", "Valve"),
        ("climate", "Climate"),
        ("lock", "Lock"),
    )

    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="entities"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True
    )

    name = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)

    subtype = models.CharField(
        max_length=50,
        blank=True,
        help_text="rgb, dimmer, speed, dht22, soil_moisture, etc"
    )

    # Flexible state (ON/OFF, numbers, RGB JSON, etc.)
    state = models.JSONField(default=dict, blank=True)

    # Declares what this entity supports
    capabilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="brightness, rgb, speed, modes, etc"
    )

    unit = models.CharField(max_length=20, blank=True)
    is_controllable = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("device", "name")

    def state_topic(self):
        return (
            f"home/{self.device.home_identifier}/"
            f"{self.device.node_name}/"
            f"{self.entity_type}/"
            f"{self.name}/state"
        )

    def command_topic(self):
        return (
            f"home/{self.device.home_identifier}/"
            f"{self.device.node_name}/"
            f"{self.entity_type}/"
            f"{self.name}/command"
        )

    def __str__(self):
        return f"{self.device.name} - {self.name}"


# 5. Entity Attributes (Multi-Value Sensors)
class EntityAttribute(models.Model):
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="attributes"
    )
    key = models.CharField(max_length=50)   # temperature, humidity, voltage
    value = models.CharField(max_length=50)
    unit = models.CharField(max_length=20, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("entity", "key")


# 6. Entity State History (Graphs & Analytics)
class EntityStateHistory(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    value = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity", "timestamp"]),
        ]


# 7. Automations (Rules Engine)
class Automation(models.Model):
    home = models.ForeignKey(Home, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    
    # Advanced automation features
    trigger_logic = models.CharField(
        max_length=3,
        choices=[('AND', 'All conditions must match'), ('OR', 'Any condition matches')],
        default='AND',
        help_text='How to combine multiple triggers'
    )
    cooldown_seconds = models.IntegerField(
        default=60,
        help_text='Minimum seconds between executions (prevents rapid re-triggering)'
    )
    created_at = models.DateTimeField(auto_now_add=True)


class AutomationTrigger(models.Model):
    TRIGGER_TYPES = [
        ('state', 'Entity State'),
        ('time', 'Time Schedule'),
        ('sun', 'Astronomical Event'),
    ]
    
    SUN_EVENTS = [
        ('sunrise', 'Sunrise'),
        ('sunset', 'Sunset'),
        ('dawn', 'Dawn'),
        ('dusk', 'Dusk'),
        ('noon', 'Solar Noon'),
    ]
    
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name="triggers"
    )
    
    # Trigger type determines which fields are used
    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPES,
        default='state',
        help_text="Type of trigger: state, time, or sun"
    )
    
    # STATE TRIGGER FIELDS (existing)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, null=True, blank=True)
    attribute = models.CharField(
        max_length=50, blank=True,
        help_text="temperature, humidity, state"
    )
    operator = models.CharField(
        max_length=10,
        choices=[
            ("==", "Equals"),
            ("!=", "Not Equals"),
            (">", "Greater Than"),
            ("<", "Less Than"),
            (">=", "Greater or Equal"),
            ("<=", "Less or Equal"),
        ],
        blank=True
    )
    value = models.JSONField(blank=True, null=True)
    
    # TIME TRIGGER FIELDS (new)
    time_of_day = models.TimeField(
        null=True, 
        blank=True,
        help_text="Time to trigger (HH:MM:SS)"
    )
    days_of_week = models.JSONField(
        null=True, 
        blank=True,
        help_text="List of days: [0-6] where 0=Monday, 6=Sunday. Empty list = every day"
    )
    
    # SUN TRIGGER FIELDS (new)
    sun_event = models.CharField(
        max_length=20,
        choices=SUN_EVENTS,
        null=True,
        blank=True,
        help_text="Astronomical event to trigger on"
    )
    sun_offset = models.IntegerField(
        default=0,
        help_text="Offset in minutes (negative = before event, positive = after)"
    )

    def __str__(self):
        if self.trigger_type == 'time':
            days_str = f" on {self.days_of_week}" if self.days_of_week else " daily"
            return f"Time: {self.time_of_day}{days_str}"
        elif self.trigger_type == 'sun':
            offset_str = f" {self.sun_offset:+d}min" if self.sun_offset != 0 else ""
            return f"Sun: {self.sun_event}{offset_str}"
        else:
            return f"{self.entity.name if self.entity else 'Unknown'} {self.operator} {self.value}"


class AutomationAction(models.Model):
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name="actions"
    )
    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, null=True, blank=True
    )
    scene = models.ForeignKey(
        'Scene', on_delete=models.CASCADE, null=True, blank=True
    )
    command = models.JSONField(
        blank=True, null=True,
        help_text="e.g. {state:'ON'} or {brightness:80}"
    )
    
    # Action delay feature
    delay_seconds = models.IntegerField(
        default=0,
        help_text='Delay before executing this action (in seconds)'
    )

    def __str__(self):
        if self.scene:
            return f"Trigger Scene: {self.scene.name}"
        return f"Control {self.entity.name}: {self.command}"


class AutomationExecution(models.Model):
    """Track automation execution history for monitoring and debugging"""
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name="executions"
    )
    executed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    trigger_entity = models.ForeignKey(
        Entity, on_delete=models.SET_NULL, null=True, blank=True
    )
    trigger_value = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['-executed_at']),
            models.Index(fields=['automation', '-executed_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.automation.name} at {self.executed_at}"


# 8. Scenes
class Scene(models.Model):
    home = models.ForeignKey(Home, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scenes', null=True, blank=True)


class SceneAction(models.Model):
    scene = models.ForeignKey(
        Scene, on_delete=models.CASCADE, related_name="actions"
    )
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    value = models.JSONField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


# 9. Scheduling (Time-based Automations)
class Schedule(models.Model):
    SCHEDULE_TYPES = (
        ("scene", "Scene"),
        ("automation", "Automation"),
        ("entity", "Entity Control"),
    )

    home = models.ForeignKey(Home, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)

    scene = models.ForeignKey('Scene', null=True, blank=True, on_delete=models.CASCADE)
    automation = models.ForeignKey(
        'Automation', null=True, blank=True, on_delete=models.CASCADE
    )
    entity = models.ForeignKey('Entity', null=True, blank=True, on_delete=models.CASCADE)

    command = models.JSONField(blank=True, null=True)

    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.schedule_type})"


# 10. Firmware & OTA Tracking
class Firmware(models.Model):
    version = models.CharField(max_length=50)
    file_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)



class OTAUpdate(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    firmware = models.ForeignKey(Firmware, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=20,
        choices=(("pending", "Pending"), ("success", "Success"), ("failed", "Failed")),
        default="pending"
    )
    updated_at = models.DateTimeField(auto_now=True)


# ============================================================================
# ENERGY MONITORING MODELS
# ============================================================================

class DevicePowerProfile(models.Model):
    """Store average power consumption for different device types"""
    entity_type = models.CharField(max_length=50, unique=True)
    average_watts = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Device Power Profile"
        verbose_name_plural = "Device Power Profiles"
    
    def __str__(self):
        return f"{self.entity_type}: {self.average_watts}W"


class EnergyLog(models.Model):
    """Track daily energy consumption per entity"""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='energy_logs')
    date = models.DateField()
    on_duration_seconds = models.IntegerField(default=0, help_text="Total seconds device was on")
    estimated_kwh = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['entity', 'date']
        ordering = ['-date']
        verbose_name = "Energy Log"
        verbose_name_plural = "Energy Logs"
        indexes = [
            models.Index(fields=['entity', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.entity.name} - {self.date}: {self.estimated_kwh} kWh"
    
    @staticmethod
    def calculate_energy(entity, duration_seconds):
        """Calculate energy consumption in kWh"""
        try:
            profile = DevicePowerProfile.objects.get(entity_type=entity.entity_type)
            watts = float(profile.average_watts)
        except DevicePowerProfile.DoesNotExist:
            # Default power consumption if no profile exists
            default_watts = {
                'light': 15,
                'fan': 75,
                'switch': 10,
            }
            watts = default_watts.get(entity.entity_type, 10)
        
        # Convert to kWh: (watts * hours) / 1000
        hours = duration_seconds / 3600
        kwh = (watts * hours) / 1000
        
        return kwh


class UserEnergySettings(models.Model):
    """Store user preferences for energy monitoring"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='energy_settings')
    electricity_rate_per_kwh = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=8.00,
        help_text="Cost per kWh in user's currency"
    )
    currency = models.CharField(max_length=3, default='INR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Energy Settings"
        verbose_name_plural = "User Energy Settings"
    
    def __str__(self):
        return f"{self.user.username}: {self.electricity_rate_per_kwh} {self.currency}/kWh"
