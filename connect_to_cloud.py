"""
Gateway-to-Cloud WebSocket Connection Script
Connects local gateway to cloud server for remote device access
"""
import asyncio
import websockets
import json
import os
import django
from asgiref.sync import sync_to_async
import paho.mqtt.publish as mqtt_publish

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from rest_framework.authtoken.models import Token
from core.models import Home, Device

CLOUD_URL = "ws://35.209.239.164:8000/ws/gateway"  # Production cloud server
LOCAL_HOME_ID = 1  # Local DB ID (Integer)
CLOUD_HOME_ID = "148d207f-e40b-495a-aab1-79dac65d95df"  # Cloud UUID (from mobile logs)

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
            entity_data = {
                'id': entity.id,
                'name': entity.name,
                'identifier': entity.name,
                'entity_type': entity.entity_type,
                'platform': None,  # Entity model may not have platform, derived from device metadata?
                'state': entity.state,
            }
            device_data['entities'].append(entity_data)
        
        device_list.append(device_data)
    
    return device_list

async def connect_to_cloud():
    """Connect local gateway to cloud WebSocket"""
    
    # Get auth token
    token = await get_auth_token()
    
    url = f"{CLOUD_URL}/{CLOUD_HOME_ID}/?token={token}"
    
    print(f"🌐 Connecting to cloud: {url}")
    
    async with websockets.connect(url) as websocket:
        print("✅ Connected to cloud!")
        
        # Listen for requests from cloud
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                request_id = data.get('request_id')
                
                print(f"📨 Cloud request: {msg_type} (ID: {request_id})")
                
                if msg_type == 'get_devices':
                    # Get devices from database
                    device_list = await get_devices_from_db(LOCAL_HOME_ID)
                    
                    # Send response
                    response = {
                        'type': 'get_devices_response',
                        'request_id': request_id,
                        'devices': device_list,
                    }
                    
                    await websocket.send(json.dumps(response))
                    print(f"✅ Sent {len(device_list)} devices to cloud")
                
                elif msg_type == 'control_entity':
                    # Handle remote control command
                    print(f"🔍 DEBUG: Full message data: {data}")  # DEBUG
                    entity_id = data.get('entity_id')
                    command = data.get('command')
                    value = data.get('value')
                    
                    print(f"🎮 Control command: Entity {entity_id}, Command: {command}, Value: {value}")
                    
                    # Get entity details from DB
                    from core.models import Entity
                    
                    @sync_to_async
                    def get_entity_data(e_id):
                        entity = Entity.objects.select_related('device').get(id=e_id)
                        return {
                            'identifier': entity.name,
                            'device_identifier': entity.device.node_name,
                            'home_identifier': entity.device.home_identifier,  # Fixed: use device.home_identifier
                            'type': entity.entity_type
                        }
                    
                    try:
                        entity_data = await get_entity_data(entity_id)
                        
                        # Construct MQTT topic
                        # Topic: home/{home_id}/{node_id}/{type}/{entity_id}/command
                        topic = f"home/{entity_data['home_identifier']}/{entity_data['device_identifier']}/{entity_data['type']}/{entity_data['identifier']}/command"
                        
                        # Construct payload - handle both formats (turn_on/turn_off or ON/OFF)
                        payload = {}
                        cmd_upper = command.upper()
                        
                        if cmd_upper in ['ON', 'TURN_ON']:
                            payload = {'power': True}
                        elif cmd_upper in ['OFF', 'TURN_OFF']:
                            payload = {'power': False}
                        elif cmd_upper == 'VALUE' and value:
                            # Mobile app sends command:'value' with value:'ON'/'OFF'
                            val_upper = str(value).upper()
                            if val_upper == 'ON':
                                payload = {'power': True}
                            elif val_upper == 'OFF':
                                payload = {'power': False}
                            else:
                                # Numeric value for dimmers, etc.
                                payload = {'value': value}
                        elif cmd_upper in ['SET_VALUE']:
                            payload = {'value': value}
                        
                        # Publish to MQTT (using paho-mqtt)
                        print(f"📤 Publishing to {topic}: {payload}")
                        
                        # Convert payload to ESPHome-compatible format
                        # ESPHome switches expect simple strings "ON"/"OFF", not JSON
                        mqtt_payload = payload
                        if isinstance(payload, dict):
                            if 'power' in payload and len(payload) == 1:
                                # {'power': True} -> "ON"
                                mqtt_payload = "ON" if payload['power'] else "OFF"
                            elif 'value' in payload and len(payload) == 1:
                                # {'value': 'ON'} -> "ON"
                                mqtt_payload = payload['value']
                            else:
                                # Complex commands (brightness, RGB, etc.) stay as JSON
                                mqtt_payload = json.dumps(payload)
                        
                        # Use simple single-shot publish since we don't have a persistent client in this script context easily accessible
                        # Note: Ideally we should use the same persistent client if possible, but for now this works
                        mqtt_publish.single(topic, mqtt_payload, hostname="127.0.0.1")
                        
                        print("✅ Command published to MQTT")
                        
                    except Exception as e:
                        print(f"❌ Error processing control command: {e}")
                    
            except Exception as e:
                print(f"❌ Error handling message: {e}")

if __name__ == "__main__":
    print("🚀 Starting gateway-to-cloud connection...")
    try:
        asyncio.run(connect_to_cloud())
    except KeyboardInterrupt:
        print("\n👋 Connection closed")
    except Exception as e:
        print(f"❌ Connection error: {e}")
