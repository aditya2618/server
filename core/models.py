from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


# 1. Home, User, Membership
class Home(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_homes")
    created_at = models.DateTimeField(auto_now_add=True)

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
    home = models.ForeignKey(Home, on_delete=models.CASCADE, related_name="devices")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True
    )

    name = models.CharField(max_length=100)
    node_name = models.CharField(
        max_length=100, unique=True,
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

    def base_topic(self):
        return f"home/{self.home.id}/{self.node_name}"

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
            f"home/{self.device.home.id}/"
            f"{self.device.node_name}/"
            f"{self.entity_type}/"
            f"{self.name}/state"
        )

    def command_topic(self):
        return (
            f"home/{self.device.home.id}/"
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
    created_at = models.DateTimeField(auto_now_add=True)


class AutomationTrigger(models.Model):
    automation = models.ForeignKey(
        Automation, on_delete=models.CASCADE, related_name="triggers"
    )
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    attribute = models.CharField(
        max_length=50, blank=True,
        help_text="temperature, humidity, state"
    )
    operator = models.CharField(
        max_length=5, choices=((">", ">"), ("<", "<"), ("==", "=="))
    )
    value = models.CharField(max_length=50)


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

    def __str__(self):
        if self.scene:
            return f"Trigger Scene: {self.scene.name}"
        return f"Control {self.entity.name}: {self.command}"


# 8. Scenes
class Scene(models.Model):
    home = models.ForeignKey(Home, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)


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
