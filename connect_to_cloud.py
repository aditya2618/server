"""
Gateway-to-Cloud WebSocket Connection Script
Connects local gateway to cloud server for remote device access.
Handles bidirectional communication:
- Cloud -> Local: Control commands (via WebSocket -> MQTT)
- Local -> Cloud: Sensor/State updates (via MQTT -> WebSocket)
"""
import asyncio
import websockets
import json
import os
import django
import sys
from asgiref.sync import sync_to_async
import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from rest_framework.authtoken.models import Token
from core.models import Home, Device, Entity

# Configuration
CLOUD_URL = "ws://35.209.239.164:8000/ws/gateway"
LOCAL_HOME_ID = 1
CLOUD_HOME_ID = "148d207f-e40b-495a-aab1-79dac65d95df"
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

# Global state
mqtt_queue = asyncio.Queue()
main_loop = None

@sync_to_async
def get_auth_token():
    """Get authentication token from database"""
    user = Token.objects.first().user
    token = Token.objects.get(user=user).key
    return token

@sync_to_async
def get_devices_from_db(home_id):
    """Get devices from database"""
    devices = Device.objects.filter(home_id=home_id)
    device_list = []
    
    for device in devices:
        device_data = {
            'id': device.id,
            'name': device.name,
            'identifier': device.node_name,
            'is_online': device.is_online,
            'last_seen': device.last_seen.isoformat() if device.last_seen else None,
            'entities': []
        }
        
        for entity in device.entities.all():
            device_data['entities'].append({
                'id': entity.id,
                'name': entity.name,
                'identifier': entity.name,
                'entity_type': entity.entity_type,
                'state': entity.state,
                'platform': getattr(device, 'platform', None)
            })
        
        device_list.append(device_data)
    
    return device_list

@sync_to_async
def resolve_entity_from_topic(topic, payload_str):
    """
    Resolve MQTT topic to Entity and construct cloud update message.
    Topic formats:
    - State: home/{home_id}/{node_name}/{entity_type}/{entity_name}/state
    - Status: home/{home_id}/{node_name}/status
    """
    parts = topic.split('/')
    
    try:
        # 1. Handle Status Update (Online/Offline)
        if topic.endswith('/status') and len(parts) == 4:
            home_ident, node_name = parts[1], parts[2]
            try:
                device = Device.objects.get(home_identifier=home_ident, node_name=node_name)
                is_online = (payload_str == 'online')
                
                return {
                    "type": "state_update",
                    "device_id": device.id,  # Local ID maps to edge_id in cloud
                    "is_online": is_online,
                }
            except Device.DoesNotExist:
                return None

        # 2. Handle Entity State Update
        elif topic.endswith('/state') and len(parts) >= 6:
            # home/{home_id}/{node_name}/{entity_type}/{entity_name}/state
            home_ident = parts[1]
            node_name = parts[2]
            entity_type = parts[3]
            entity_name = parts[4]
            
            try:
                # Resolve Entity
                entity = Entity.objects.select_related('device').get(
                    device__home_identifier=home_ident,
                    device__node_name=node_name,
                    entity_type=entity_type,
                    name=entity_name
                )
                
                # Parse Payload
                try:
                    state_value = json.loads(payload_str)
                except json.JSONDecodeError:
                    state_value = payload_str
                
                return {
                    "type": "state_update",
                    "entity_id": entity.id, # Local ID -> Cloud edge_id
                    "state": state_value,
                    "is_online": True # Implicitly online if sending state
                }
                
            except Entity.DoesNotExist:
                return None
                
    except Exception as e:
        print(f"Error resolving topic {topic}: {e}")
        return None

# MQTT Callbacks
def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✓ MQTT Listener connected")
        client.subscribe("home/+/+/+/+/state")
        client.subscribe("home/+/+/status")
    else:
        print(f"✗ MQTT Listener connection failed: {rc}")

def on_mqtt_message(client, userdata, msg):
    """Queue MQTT message for processing in main loop"""
    if main_loop:
        try:
            payload_str = msg.payload.decode()
            main_loop.call_soon_threadsafe(mqtt_queue.put_nowait, (msg.topic, payload_str))
        except Exception as e:
            print(f"Error queuing MQTT message: {e}")

async def cloud_producer(websocket):
    """Read from MQTT queue and send to Cloud"""
    print("🚀 Started Cloud Producer (Local -> Cloud)")
    while True:
        try:
            topic, payload_str = await mqtt_queue.get()
            
            # Resolve to Cloud Message
            cloud_msg = await resolve_entity_from_topic(topic, payload_str)
            
            if cloud_msg:
                # Add request_id for tracing
                cloud_msg['request_id'] = f"mqtt_{os.urandom(4).hex()}"
                
                await websocket.send(json.dumps(cloud_msg))
                # print(f"📤 Sent update to cloud: {cloud_msg['type']} (Entity: {cloud_msg.get('entity_id')})")
                
            mqtt_queue.task_done()
            
        except Exception as e:
            print(f"Error in producer: {e}")
            await asyncio.sleep(1)

@sync_to_async
def get_entity_details(entity_id):
    """Get entity identifiers for control command"""
    try:
        entity = Entity.objects.select_related('device').get(id=entity_id)
        return {
            'identifier': entity.name,
            'device_identifier': entity.device.node_name,
            'home_identifier': entity.device.home_identifier,
            'type': entity.entity_type
        }
    except Entity.DoesNotExist:
        return None

async def cloud_consumer(websocket):
    """Read from Cloud and process commands (Cloud -> Local)"""
    print("🚀 Started Cloud Consumer (Cloud -> Local)")
    async for message in websocket:
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            request_id = data.get('request_id')
            
            # print(f"📨 Cloud request: {msg_type} (ID: {request_id})")
            
            if msg_type == 'get_devices':
                device_list = await get_devices_from_db(LOCAL_HOME_ID)
                response = {
                    'type': 'get_devices_response',
                    'request_id': request_id,
                    'devices': device_list,
                }
                await websocket.send(json.dumps(response))
                print(f"✅ Sent {len(device_list)} devices to cloud")
            
            elif msg_type == 'control_entity':
                entity_id = data.get('entity_id')
                command = data.get('command')
                value = data.get('value')
                
                print(f"🎮 Control: Entity {entity_id}, Cmd: {command}, Val: {value}")
                
                entity_data = await get_entity_details(entity_id)
                if not entity_data:
                    print(f"❌ Entity {entity_id} not found")
                    continue
                
                # Construct MQTT topic
                topic = f"home/{entity_data['home_identifier']}/{entity_data['device_identifier']}/{entity_data['type']}/{entity_data['identifier']}/command"
                
                # Construct payload
                payload = {}
                cmd_upper = command.upper()
                
                if cmd_upper in ['ON', 'TURN_ON']:
                    payload = {'power': True}
                elif cmd_upper in ['OFF', 'TURN_OFF']:
                    payload = {'power': False}
                elif cmd_upper == 'VALUE' and value:
                    val_upper = str(value).upper()
                    if val_upper == 'ON':
                        payload = {'power': True}
                    elif val_upper == 'OFF':
                        payload = {'power': False}
                    else:
                        payload = {'value': value}
                elif cmd_upper in ['SET_VALUE']:
                    payload = {'value': value}
                
                # Convert to ESPHome format (String vs JSON)
                mqtt_payload = payload
                if isinstance(payload, dict):
                    if 'power' in payload and len(payload) == 1:
                        mqtt_payload = "ON" if payload['power'] else "OFF"
                    elif 'value' in payload and len(payload) == 1:
                        mqtt_payload = payload['value']
                    else:
                        mqtt_payload = json.dumps(payload)
                
                # Publish
                print(f"📤 Publishing to {topic}: {mqtt_payload}")
                mqtt_publish.single(topic, mqtt_payload, hostname=MQTT_BROKER)
                
        except Exception as e:
            print(f"❌ Error handling message: {e}")

async def connect_to_cloud():
    """Main connection loop with auto-reconnect"""
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    # Start MQTT Listener
    client = mqtt_client.Client()
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()  # Runs in background thread
    except Exception as e:
        print(f"❌ Failed to start MQTT listener: {e}")
        return

    while True:
        try:
            token = await get_auth_token()
            url = f"{CLOUD_URL}/{CLOUD_HOME_ID}/?token={token}"
            
            print(f"🌐 Connecting to cloud...")
            
            async with websockets.connect(url) as websocket:
                print("✅ Connected to cloud!")
                
                # Run producer and consumer concurrently
                consumer_task = asyncio.create_task(cloud_consumer(websocket))
                producer_task = asyncio.create_task(cloud_producer(websocket))
                
                # Wait for any task to finish (usually error or close)
                done, pending = await asyncio.wait(
                    [consumer_task, producer_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    
        except (websockets.ConnectionClosed, ConnectionRefusedError) as e:
            print(f"⚠️ Cloud disconnected: {e}. Reconnecting in 5s...")
        except Exception as e:
            print(f"❌ Unexpected error: {e}. Reconnecting in 5s...")
            
        await asyncio.sleep(5)

if __name__ == "__main__":
    print("🚀 Starting Smart Home Bridge...")
    try:
        asyncio.run(connect_to_cloud())
    except KeyboardInterrupt:
        print("\n👋 Stopping...")
