from core.mqtt.client import publish_command


def control_entity(entity, value):
    """
    Control an entity by publishing a command to its MQTT topic.
    
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
    publish_command(topic, value)
    print(f"🔵 publish_command completed for entity {entity.id}")

