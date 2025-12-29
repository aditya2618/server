from core.models import Device, Entity, EntityAttribute, EntityStateHistory

print("=== MQTT TEST VERIFICATION ===\n")

# Check Device
device = Device.objects.get(node_name="node_1")
print(f"Device: {device.name}")
print(f"  Online: {device.is_online}")
print(f"  Last Seen: {device.last_seen}")

# Check Entity
entity = Entity.objects.get(device=device, name="test")
print(f"\nEntity: {entity.name} ({entity.entity_type})")
print(f"  State: {entity.state}")

# Check Attributes
print(f"\nAttributes:")
for attr in EntityAttribute.objects.filter(entity=entity):
    print(f"  {attr.key}: {attr.value} {attr.unit}")

# Check History
print(f"\nHistory (latest 3):")
for hist in EntityStateHistory.objects.filter(entity=entity).order_by('-timestamp')[:3]:
    print(f"  {hist.timestamp}: {hist.value}")

print(f"\n✓ Total history records: {EntityStateHistory.objects.filter(entity=entity).count()}")
