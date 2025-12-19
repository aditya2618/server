"""
Test MQTT Command Publishing to ESP32
This script publishes a command to the ESP32 and monitors for state updates.
"""
import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Topics
COMMAND_TOPIC = "home/testlast/aditya_test_111/switch/light1/command"
STATE_TOPIC = "home/testlast/aditya_test_111/switch/light1/state"
ALL_TOPICS = "home/#"

received_messages = []

def on_connect(client, userdata, flags, rc):
    print(f"✓ Connected to MQTT broker (rc={rc})")
    # Subscribe to all topics to see what's happening
    client.subscribe(ALL_TOPICS)
    print(f"✓ Subscribed to {ALL_TOPICS}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] 📥 {topic} → {payload}")
    received_messages.append((topic, payload, timestamp))

def main():
    print("="*60)
    print("ESP32 MQTT Command Test")
    print("="*60)
    
    # Create MQTT client
    client = mqtt.Client(client_id="test_publisher")
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Connect
    print(f"\n🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    # Wait for connection
    time.sleep(2)
    
    # Monitor for 5 seconds to see existing traffic
    print("\n👀 Monitoring MQTT traffic for 5 seconds...")
    time.sleep(5)
    
    # Publish OFF command
    print(f"\n📤 Publishing OFF command to: {COMMAND_TOPIC}")
    command = {"value": "OFF"}
    client.publish(COMMAND_TOPIC, json.dumps(command))
    print(f"   Payload: {json.dumps(command)}")
    
    # Wait for response
    print("\n⏳ Waiting 10 seconds for ESP32 response...")
    time.sleep(10)
    
    # Publish ON command
    print(f"\n📤 Publishing ON command to: {COMMAND_TOPIC}")
    command = {"value": "ON"}
    client.publish(COMMAND_TOPIC, json.dumps(command))
    print(f"   Payload: {json.dumps(command)}")
    
    # Wait for response
    print("\n⏳ Waiting 10 seconds for ESP32 response...")
    time.sleep(10)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    # Check if we received state updates
    state_updates = [m for m in received_messages if 'state' in m[0] and 'light' in m[0]]
    sensor_updates = [m for m in received_messages if 'sensor' in m[0]]
    
    print(f"\n📊 Total messages received: {len(received_messages)}")
    print(f"   - Sensor updates: {len(sensor_updates)}")
    print(f"   - Switch state updates: {len(state_updates)}")
    
    if state_updates:
        print("\n✅ ESP32 IS responding with state updates!")
        print("   Recent state updates:")
        for topic, payload, ts in state_updates[-5:]:
            print(f"   [{ts}] {topic} → {payload}")
    else:
        print("\n❌ ESP32 NOT responding with state updates")
        print("   This means ESP32 is either:")
        print("   1. Not subscribed to command topics")
        print("   2. Not publishing state updates")
        print("   3. Using different topic format")
    
    if sensor_updates:
        print("\n✅ ESP32 IS publishing sensor data")
        print("   This confirms ESP32 is connected to MQTT")
    
    # Cleanup
    client.loop_stop()
    client.disconnect()
    print("\n✓ Disconnected from MQTT broker")

if __name__ == "__main__":
    main()
