"""
Create test data for MQTT testing
Run: python manage.py shell < create_test_data.py
"""

from django.contrib.auth.models import User
from core.models import Home, Device, Entity

# Create or get user
user, _ = User.objects.get_or_create(username="admin")

# Create home
home, _ = Home.objects.get_or_create(
    id=1,
    defaults={"name": "Test Home", "owner": user}
)

# Create device
device, _ = Device.objects.get_or_create(
    node_name="node_1",
    defaults={
        "home": home,
        "name": "Test ESP32 Node 1"
    }
)

# Create test sensor entity
entity, _ = Entity.objects.get_or_create(
    device=device,
    name="test",
    defaults={
        "entity_type": "sensor",
        "subtype": "dht22",
        "is_controllable": False
    }
)

print(f"✓ Created/Updated:")
print(f"  Home: {home}")
print(f"  Device: {device}")
print(f"  Entity: {entity}")
print(f"\nTest with:")
print(f'  mosquitto_pub -t "home/1/node_1/sensor/test/state" -m \'{{"temperature":25.6,"humidity":62}}\'')
