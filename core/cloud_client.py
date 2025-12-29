"""
Cloud WebSocket Client for Local Gateway

Connects local gateway to cloud server for remote access.
This runs on the local server (Raspberry Pi) and maintains
a persistent connection to the cloud.

Features:
- Auto-connect on startup
- Auto-reconnect with exponential backoff
- Heartbeat/ping every 30 seconds
- Command queue for offline resilience
- Forward entity states to cloud
"""
import asyncio
import websockets
import json
import uuid
import logging
from datetime import datetime
from django.conf import settings
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class CloudClient:
    """WebSocket client for connecting gateway to cloud"""
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 60  # Max 60 seconds
        self.home_id = None
        self.gateway_secret = None
        self.running = False
        
    async def start(self):
        """Start the cloud client"""
        # Load configuration
        if not settings.CLOUD_ENABLED:
            logger.info("☁️  Cloud bridge is disabled")
            return
        
        cloud_url = settings.CLOUD_BRIDGE_URL
        self.home_id = settings.CLOUD_GATEWAY_ID
        self.gateway_id = getattr(settings, 'CLOUD_GATEWAY_UUID', None)
        self.gateway_secret = settings.CLOUD_GATEWAY_SECRET
        
        if not self.gateway_secret:
            logger.warning("⚠️  Cloud credentials not configured")
            return
        
        logger.info(f"☁️  Starting cloud client for home: {self.home_id} (GW: {self.gateway_id})")
        self.running = True
        
        # Start connection loop
        asyncio.create_task(self.connection_loop())
        
    async def connection_loop(self):
        """Main connection loop with auto-reconnect"""
        while self.running:
            try:
                await self.connect_and_listen()
            except Exception as e:
                logger.error(f"☁️  Connection error: {e}")
                
            if self.running:
                logger.info(f"☁️  Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                
                # Exponential backoff
                self.reconnect_delay = min(
                    self.reconnect_delay * 2,
                    self.max_reconnect_delay
                )
    
    async def connect_and_listen(self):
        """Connect to cloud and listen for messages"""
        # Build WebSocket URL
        # Prefer actual gateway UUID, fallback to home_id for legacy
        gid = self.gateway_id or self.home_id
        url = f"{settings.CLOUD_BRIDGE_URL}?gateway_id={gid}&secret={self.gateway_secret}"
        
        logger.info(f"☁️  Connecting to cloud: {settings.CLOUD_BRIDGE_URL}")
        
        async with websockets.connect(url) as ws:
            self.ws = ws
            self.connected = True
            self.reconnect_delay = 1  # Reset backoff on successful connection
            
            logger.info(f"✅ Connected to cloud!")
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self.heartbeat())
            
            try:
                # Listen for messages
                async for message in ws:
                    await self.handle_message(message)
            finally:
                heartbeat_task.cancel()
                self.connected = False
                logger.info("☁️  Disconnected from cloud")
    
    async def heartbeat(self):
        """Send periodic pings to keep connection alive"""
        while self.connected:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                if self.ws and self.connected:
                    await self.send_message({
                        'type': 'ping',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"☁️  Heartbeat error: {e}")
                break
    
    async def handle_message(self, message):
        """Handle incoming message from cloud"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            logger.info(f"☁️  Received: {msg_type}")
            
            if msg_type == 'pong':
                # Heartbeat response
                pass
            
            elif msg_type == 'get_devices':
                # Cloud asking for device list
                await self.send_device_list(data.get('request_id'))
            
            elif msg_type == 'control_entity':
                # Cloud sending control command
                await self.handle_control_command(data)
            
            elif msg_type == 'run_scene':
                # Cloud asking to run a scene
                await self.handle_run_scene(data)
            
            else:
                logger.warning(f"☁️  Unknown message type: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"☁️  Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"☁️  Message handling error: {e}")
    
    async def send_message(self, data):
        """Send message to cloud"""
        if self.ws and self.connected:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"☁️  Send error: {e}")
    
    async def send_device_list(self, request_id):
        """Send device/entity list to cloud"""
        from core.models import Entity, Home
        
        # Get all entities for this home
        try:
            # We assume single home for this gateway
            home = await sync_to_async(Home.objects.first)()
            if not home:
                logger.warning("No home found locally!")
                return

            logger.info(f"Syncing entities for home: {home.name}")
            entities = await sync_to_async(list)(
                Entity.objects.filter(device__home=home).select_related('device')
            )
            
            device_list = []
            for entity in entities:
                device_list.append({
                    'id': str(entity.id),
                    'name': entity.name,
                    'entity_type': entity.entity_type,
                    'state': entity.state,
                    'device_name': entity.device.name,
                })
            
            await self.send_message({
                'type': 'devices_response',
                'request_id': request_id,
                'devices': device_list
            })
            
            logger.info(f"☁️  Sent {len(device_list)} devices to cloud")
            
        except Exception as e:
            logger.error(f"☁️  Error getting devices: {e}")
            await self.send_message({
                'type': 'error',
                'request_id': request_id,
                'message': str(e)
            })
    
    async def handle_control_command(self, data):
        """Handle entity control command from cloud"""
        from core.mqtt.publisher import send_entity_command
        from core.models import Entity
        
        entity_id = data.get('entity_id')
        command = data.get('command')
        value = data.get('value')
        request_id = data.get('request_id')
        
        logger.info(f"☁️  Control command: entity={entity_id}, cmd={command}, val={value}")
        
        try:
            # Get entity
            entity = await sync_to_async(Entity.objects.get)(id=entity_id)
            
            # Send command via MQTT
            result = await sync_to_async(send_entity_command)(
                entity=entity,
                command=command,
                value=value
            )
            
            # Send acknowledgment
            await self.send_message({
                'type': 'ack',
                'request_id': request_id,
                'status': 'success',
                'message': f'Command sent to {entity.name}'
            })
            
        except Entity.DoesNotExist:
            logger.error(f"☁️  Entity not found: {entity_id}")
            await self.send_message({
                'type': 'error',
                'request_id': request_id,
                'message': f'Entity {entity_id} not found'
            })
        except Exception as e:
            logger.error(f"☁️  Control error: {e}")
            await self.send_message({
                'type': 'error',
                'request_id': request_id,
                'message': str(e)
            })
    
    async def handle_run_scene(self, data):
        """Handle run scene command from cloud"""
        from core.models import Scene
        
        scene_id = data.get('scene_id')
        request_id = data.get('request_id')
        
        logger.info(f"☁️  Running scene: {scene_id}")
        
        try:
            # Get scene
            scene = await sync_to_async(Scene.objects.get)(id=scene_id)
            
            # Execute scene (this will trigger MQTT commands)
            await sync_to_async(scene.execute)()
            
            # Send acknowledgment
            await self.send_message({
                'type': 'ack',
                'request_id': request_id,
                'status': 'success',
                'message': f'Scene "{scene.name}" executed'
            })
            
        except Scene.DoesNotExist:
            logger.error(f"☁️  Scene not found: {scene_id}")
            await self.send_message({
                'type': 'error',
                'request_id': request_id,
                'message': f'Scene {scene_id} not found'
            })
        except Exception as e:
            logger.error(f"☁️  Scene execution error: {e}")
            await self.send_message({
                'type': 'error',
                'request_id': request_id,
                'message': str(e)
            })
    
    async def broadcast_state_update(self, entity_id, state):
        """Broadcast entity state update to cloud (if connected)"""
        if self.connected:
            await self.send_message({
                'type': 'state_update',
                'entity_id': entity_id,
                'state': state,
                'timestamp': datetime.now().isoformat()
            })
    
    async def stop(self):
        """Stop the cloud client"""
        logger.info("☁️  Stopping cloud client")
        self.running = False
        if self.ws:
            await self.ws.close()


# Global instance
cloud_client = CloudClient()


def start_cloud_client():
    """Start cloud client (call this from Django startup)"""
    asyncio.create_task(cloud_client.start())
