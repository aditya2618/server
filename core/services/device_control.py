from core.mqtt.client import publish_command
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def control_entity(entity, value):
    """
    Control an entity by publishing a command to its MQTT topic.
    Also updates entity state and broadcasts via WebSocket.
    
    Args:
        entity: Entity model instance
        value: Command value (dict for complex commands, string for simple)
        
    Examples:
        control_entity(light, "ON")
        control_entity(light, {"brightness": 80})
        control_entity(rgb_light, {"state": "ON", "r": 255, "g": 100, "b": 50})
    """
    topic = entity.command_topic()
    print(f"🔵 control_entity called: entity_id={entity.id}, name={entity.name}, topic={topic}, value={value}")
    
    # Publish MQTT command
    publish_command(topic, value)
    print(f"🔵 publish_command completed for entity {entity.id}")
    
    # Update entity state optimistically
    if isinstance(value, dict):
        entity.state.update(value)
    else:
        entity.state['value'] = value
    entity.save(update_fields=['state'])
    print(f"💾 State updated for entity {entity.id}: {entity.state}")
    
    # Broadcast state change via WebSocket
    try:
        channel_layer = get_channel_layer()
        home_id = entity.device.home.id
        
        async_to_sync(channel_layer.group_send)(
            f"home_{home_id}",
            {
                "type": "send_state_update",
                "data": {
                    "type": "entity_state",
                    "entity_id": entity.id,
                    "device_id": entity.device.id,
                    "state": entity.state,
                    "is_online": entity.device.is_online
                }
            }
        )
        print(f"📡 WebSocket broadcast sent for entity {entity.id}")
    except Exception as e:
        print(f"⚠️ WebSocket broadcast failed: {e}")
