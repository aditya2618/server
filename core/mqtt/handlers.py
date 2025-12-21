import json
from django.utils.timezone import now
from core.mqtt.parser import parse_topic
from core.models import Device, Entity, EntityAttribute, EntityStateHistory


def infer_capabilities(value, entity_type):
    """
    Infer entity capabilities from payload and entity type.
    
    Returns dict of capabilities like {"brightness": True, "rgb": True}
    """
    caps = {}

    if entity_type in ["light", "fan"]:
        if isinstance(value, dict):
            if "brightness" in value:
                caps["brightness"] = True
            if all(k in value for k in ["r", "g", "b"]):
                caps["rgb"] = True
            if "speed" in value:
                caps["speed"] = True

    if entity_type == "sensor":
        caps["read_only"] = True

    return caps


def handle_state_message(topic, payload):
    """
    Handle incoming MQTT state message with auto-discovery.
    
    Automatically creates Device and Entity if they don't exist.
    Updates Entity state, creates history, updates attributes, and marks device online.
    """
    parsed = parse_topic(topic)
    if not parsed:
        print(f"Invalid topic format: {topic}")
        return

    home_id = parsed["home_id"]
    node_name = parsed["node_name"]
    entity_type = parsed["entity_type"]
    entity_name = parsed["entity_name"]

    # Parse payload safely
    try:
        value = json.loads(payload)
    except Exception:
        value = payload

    try:
        # Auto-create device if it doesn't exist
        device, device_created = Device.objects.get_or_create(
            home_identifier=home_id,  # Use string directly
            node_name=node_name,
            defaults={"name": node_name}
        )
        
        if device_created:
            print(f"🆕 Auto-created device: {node_name} (home={home_id})")

        # Auto-create entity if it doesn't exist
        entity, entity_created = Entity.objects.get_or_create(
            device=device,
            entity_type=entity_type,
            name=entity_name,
            defaults={
                "is_controllable": entity_type in ["light", "switch", "fan", "relay", "valve"],
                "state": {},
            }
        )

        if entity_created:
            # Infer capabilities on first creation
            entity.capabilities = infer_capabilities(value, entity_type)
            entity.save(update_fields=["capabilities"])
            print(f"🆕 Auto-created entity: {entity_type}/{entity_name} with capabilities: {entity.capabilities}")

        # Store old state for energy tracking
        old_state = entity.state.copy() if entity.state else {}
        
        # Update entity state
        entity.state = value if isinstance(value, dict) else {"value": value}
        entity.save(update_fields=["state"])

        # Store history
        EntityStateHistory.objects.create(
            entity=entity,
            value=entity.state
        )
        
        # Track energy consumption (if device turned off)
        try:
            from core.services.energy_tracker import EnergyTracker
            EnergyTracker.track_state_change(entity, old_state, entity.state)
        except Exception as e:
            print(f"⚠️ Energy tracking error: {e}")

        # Multi-value attributes (optional)
        if isinstance(value, dict):
            for k, v in value.items():
                EntityAttribute.objects.update_or_create(
                    entity=entity,
                    key=k,
                    defaults={"value": str(v)}
                )

        # Mark device online
        device.last_seen = now()
        device.is_online = True
        device.save(update_fields=["last_seen", "is_online"])

        print(f"✓ Updated {entity_type}/{entity_name} on {node_name}: {value}")
        
        # AUTOMATION: Check for triggered automations
        print(f"🤖 AUTOMATION CHECK: entity_id={entity.id}, value={value}")
        try:
            from core.automation_executor import check_automations_for_entity
            
            # Determine attribute name for automation checking
            # For sensors like "room_temp_and_humidity_temperature", extract "temperature"
            # For switches/lights, use "state"
            if entity_type == 'sensor' and '_' in entity_name:
                # Extract attribute from sensor name (last part)
                # e.g., "room_temp_and_humidity_temperature" -> "temperature"
                attribute_name = entity_name.split('_')[-1]
            else:
                attribute_name = 'state'
            
            # Extract value
            if isinstance(value, dict):
                # For complex values, check each attribute
                for attr_key, attr_value in value.items():
                    print(f"  → Checking automation for {attr_key}={attr_value}")
                    check_automations_for_entity(entity.id, attr_key, attr_value)
            else:
                # For simple values, use determined attribute name
                print(f"  → Checking automation for {attribute_name}={value}")
                check_automations_for_entity(entity.id, attribute_name, value)
            
            print(f"  ✓ Automation check complete")
        except Exception as e:
            print(f"⚠️  ERROR in automation checking: {e}")
            import traceback
            traceback.print_exc()
        
        # Push state update to WebSocket clients
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        # Get home_id for WebSocket group
        if device.home:
            home_identifier = str(device.home.id)
        elif device.home_identifier:
            # Use string home_identifier directly
            home_identifier = str(device.home_identifier)
        else:
            # No home identifier available, skip broadcast
            print(f"⚠️ Cannot broadcast: device has no home_identifier")
            return

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"home_{home_identifier}",
            {
                "type": "send_state_update",
                "data": {
                    "type": "entity_state",
                    "entity_id": entity.id,
                    "state": entity.state,
                    "device_id": device.id,
                    "is_online": device.is_online,
                }
            }
        )

    except Exception as e:
        print(f"✗ Error handling message: {e}")
        import traceback
        traceback.print_exc()


def handle_status_message(topic, payload):
    """
    Handle device status messages (LWT - Last Will & Testament).
    
    Topic format: home/<home_id>/<node_name>/status
    Payload: "online" or "offline"
    """
    parts = topic.split("/")
    if len(parts) != 4:
        print(f"Invalid status topic format: {topic}")
        return

    home_id = parts[1]
    node_name = parts[2]

    try:
        # Query device using home_identifier directly
        device = Device.objects.get(
            home_identifier=home_id,  # Use string directly
            node_name=node_name
        )

        if payload == "online":
            device.is_online = True
            device.last_seen = now()
            print(f"✓ Device {node_name} came ONLINE")
        else:
            device.is_online = False
            print(f"✗ Device {node_name} went OFFLINE")

        device.save(update_fields=["is_online", "last_seen"])
        
        # Push device status update to WebSocket clients
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        # Get home_id for WebSocket group
        if device.home:
            home_identifier = str(device.home.id)
        elif device.home_identifier:
            # Use string home_identifier directly
            home_identifier = str(device.home_identifier)
        else:
            # No home identifier available, skip broadcast
            print(f"⚠️ Cannot broadcast: device has no home_identifier")
            return

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"home_{home_identifier}",
            {
                "type": "send_state_update",
                "data": {
                    "type": "device_status",
                    "device_id": device.id,
                    "is_online": device.is_online,
                }
            }
        )

    except Device.DoesNotExist:
        print(f"✗ Device not found for status update: {node_name} (home={home_id})")

