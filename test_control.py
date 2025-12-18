from core.models import Entity
from core.services.device_control import control_entity

print("=== TESTING MQTT CONTROL ===\n")

# Get an entity to control
entity = Entity.objects.filter(entity_type='light').first()

if entity:
    print(f"Testing with entity: {entity.name} ({entity.entity_type})")
    print(f"Command topic: {entity.command_topic()}")
    print(f"Current state: {entity.state}\n")
    
    # Test simple ON command
    print("Sending command: ON")
    control_entity(entity, "ON")
    
    print("\nMessage published to MQTT!")
    print("Check mosquitto_sub output to verify.")
else:
    print("No light entities found. Create one first.")
