from core.models import Device, Entity

print("=== AUTO-DISCOVERY VERIFICATION ===\n")

# Check for auto-created device
try:
    device = Device.objects.get(node_name="node_auto_test")
    print(f"✓ Device auto-created:")
    print(f"  Name: {device.name}")
    print(f"  Node: {device.node_name}")
    print(f"  Home: {device.home_id}")
    print(f"  Online: {device.is_online}")
    
    # Check for auto-created entity
    try:
        entity = Entity.objects.get(device=device, name="ceiling")
        print(f"\n✓ Entity auto-created:")
        print(f"  Name: {entity.name}")
        print(f"  Type: {entity.entity_type}")
        print(f"  Controllable: {entity.is_controllable}")
        print(f"  Capabilities: {entity.capabilities}")
        print(f"  State: {entity.state}")
    except Entity.DoesNotExist:
        print("\n✗ Entity 'ceiling' not created")
        
except Device.DoesNotExist:
    print("✗ Device 'node_auto_test' not created")
    print("\nAll devices:")
    for d in Device.objects.all():
        print(f"  - {d.node_name}")
