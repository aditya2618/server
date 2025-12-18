def parse_topic(topic: str):
    """
    Parse MQTT topic format: home/<home_id>/<node>/<entity_type>/<entity>/state
    
    Returns dict with home_id, node_name, entity_type, entity_name
    Returns None if topic format is invalid
    """
    parts = topic.split("/")
    if len(parts) != 6:
        return None

    return {
        "home_id": parts[1],
        "node_name": parts[2],
        "entity_type": parts[3],
        "entity_name": parts[4],
    }
