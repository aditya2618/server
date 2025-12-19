import paho.mqtt.client as mqtt

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    """Called when connected to MQTT broker"""
    if rc == 0:
        print(f"✓ MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe("home/+/+/+/+/state")
        client.subscribe("home/+/+/status")
        print("✓ Subscribed to state and status topics")
    else:
        print(f"✗ MQTT connection failed with code: {rc}")


def on_message(client, userdata, msg):
    """Called when a message is received"""
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic.endswith("/status"):
        from core.mqtt.handlers import handle_status_message
        handle_status_message(topic, payload)
    else:
        from core.mqtt.handlers import handle_state_message
        handle_state_message(topic, payload)


def start_mqtt():
    """Start MQTT client and connect to broker"""
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()
        print("✓ MQTT client started")
    except Exception as e:
        print(f"✗ Failed to start MQTT client: {e}")


def publish_command(topic: str, payload):
    """
    Publish a command to an MQTT topic.
    
    Args:
        topic: MQTT topic to publish to
        payload: Command payload (dict or string)
    
    ESPHome expects:
    - Simple strings for switches: "ON"/"OFF"
    - JSON for lights with attributes: {"state": "ON", "brightness": 255, "color": {"r": 255, "g": 0, "b": 0}}
    """
    import json
    
    # Convert payload to ESPHome-compatible format
    if isinstance(payload, dict):
        # Check if this is a simple power command
        if 'value' in payload and len(payload) == 1:
            # {"value": "ON"} -> "ON"
            payload = payload['value']
        elif 'power' in payload and len(payload) == 1:
            # {"power": "ON"} -> "ON"
            payload = payload['power']
        elif 'state' in payload and len(payload) == 1:
            # {"state": "ON"} -> "ON"
            payload = payload['state']
        else:
            # For complex commands (brightness, RGB, etc.), send as JSON
            # ESPHome light component expects JSON format for complex commands
            payload = json.dumps(payload)
    
    try:
        client.publish(topic, payload)
        print(f"✓ Published command to {topic}: {payload}")
    except Exception as e:
        print(f"✗ Failed to publish command: {e}")

