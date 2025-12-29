"""
Cloud Bridge Client - Edge Gateway Side

This WebSocket client runs on the local Django server (edge gateway).
It connects TO the cloud server and maintains a persistent connection.
Commands from remote users flow THROUGH this connection.
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class CloudBridgeClient:
    """
    WebSocket client for cloud bridge connection.
    
    Maintains persistent connection to cloud server and:
    - Sends heartbeat ping every 30s
    - Receives remote commands
    - Executes commands locally
    - Sends ACK responses
    """
    
    def __init__(self, cloud_url, gateway_id, secret):
        """
        Initialize bridge client.
        
        Args:
            cloud_url: WebSocket URL (wss://cloud.example.com/bridge/)
            gateway_id: Gateway UUID from provisioning
            secret: Gateway secret from provisioning
        """
        self.cloud_url = cloud_url
        self.gateway_id = gateway_id
        self.secret = secret
        self.websocket = None
        self.running = False
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_delay = 60
        self.ping_interval = 30  # seconds
        
    async def connect(self):
        """Establish WebSocket connection to cloud."""
        url = f"{self.cloud_url}?gateway_id={self.gateway_id}&secret={self.secret}"
        logger.info(f"🔄 Connecting to cloud bridge: {self.cloud_url}")
        
        try:
            self.websocket = await websockets.connect(url)
            logger.info(f"✅ Connected to cloud bridge")
            self.reconnect_delay = 5  # Reset delay on successful connection
            return True
        except Exception as e:
            logger.error(f"❌ Bridge connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("🔌 Disconnected from cloud bridge")
    
    async def send_message(self, message):
        """Send message to cloud."""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
                logger.debug(f"📤 Sent to cloud: {message.get('type')}")
            except Exception as e:
                logger.error(f"❌ Error sending message: {e}")
    
    async def send_ping(self):
        """Send heartbeat ping to cloud."""
        await self.send_message({
            'type': 'ping',
            'timestamp': datetime.now().isoformat()
        })
    
    async def send_ack(self, request_id, status='success', data=None):
        """Send command acknowledgment to cloud."""
        await self.send_message({
            'type': 'ack',
            'request_id': request_id,
            'status': status,
            'data': data or {}
        })
    
    async def handle_command(self, message):
        """
        Handle incoming command from cloud.
        
        Message format:
        {
            "type": "command",
            "request_id": "uuid",
            "payload": {
                "entity_id": 123,
                "action": "on",
                "value": {...}
            }
        }
        """
        try:
            request_id = message.get('request_id')
            payload = message.get('payload', {})
            
            entity_id = payload.get('entity_id')
            command = payload.get('value', {})
            
            logger.info(f"📥 Command from cloud: entity={entity_id}, cmd={command}")
            
            # Execute command locally
            from core.services.device_control import control_entity
            from core.models import Entity
            
            try:
                entity = Entity.objects.get(id=entity_id)
                control_entity(entity, command)
                
                # Send success ACK
                await self.send_ack(request_id, 'success', {
                    'entity_id': entity_id,
                    'state': entity.state
                })
                logger.info(f"✅ Command executed: entity={entity_id}")
                
            except Entity.DoesNotExist:
                await self.send_ack(request_id, 'error', {
                    'message': f'Entity {entity_id} not found'
                })
                logger.error(f"❌ Entity not found: {entity_id}")
            except Exception as e:
                await self.send_ack(request_id, 'error', {
                    'message': str(e)
                })
                logger.error(f"❌ Command execution failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error handling command: {e}")
    
    async def receive_loop(self):
        """Listen for messages from cloud."""
        try:
            async for message_text in self.websocket:
                try:
                    message = json.loads(message_text)
                    message_type = message.get('type')
                    
                    logger.debug(f"📨 Received from cloud: {message_type}")
                    
                    if message_type == 'pong':
                        # Heartbeat response
                        logger.debug("💓 Pong received")
                    
                    elif message_type == 'command':
                        # Remote control command
                        await self.handle_command(message)
                    
                    elif message_type == 'sync_request':
                        # Cloud requesting data sync
                        # TODO: Implement sync
                        logger.info("🔄 Sync request from cloud")
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON from cloud")
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ Connection closed by cloud")
        except Exception as e:
            logger.error(f"❌ Receive loop error: {e}")
    
    async def ping_loop(self):
        """Send periodic heartbeat pings."""
        while self.running:
            await asyncio.sleep(self.ping_interval)
            if self.websocket:
                await self.send_ping()
    
    async def run(self):
        """
        Main run loop with auto-reconnect.
        Maintains connection and handles messages.
        """
        self.running = True
        
        while self.running:
            # Connect to cloud
            connected = await self.connect()
            
            if connected:
                try:
                    # Run receive and ping loops concurrently
                    await asyncio.gather(
                        self.receive_loop(),
                        self.ping_loop()
                    )
                except Exception as e:
                    logger.error(f"❌ Bridge error: {e}")
                finally:
                    await self.disconnect()
            
            if self.running:
                # Exponential backoff for reconnection
                logger.info(f"🔄 Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    async def stop(self):
        """Stop the bridge client."""
        self.running = False
        await self.disconnect()
        logger.info("🛑 Bridge client stopped")


# Global bridge client instance
_bridge_client = None


def get_bridge_client():
    """Get or create global bridge client instance."""
    global _bridge_client
    
    if _bridge_client is None:
        # Load settings
        cloud_url = getattr(settings, 'CLOUD_BRIDGE_URL', None)
        gateway_id = getattr(settings, 'CLOUD_GATEWAY_ID', None)
        gateway_secret = getattr(settings, 'CLOUD_GATEWAY_SECRET', None)
        
        if cloud_url and gateway_id and gateway_secret:
            _bridge_client = CloudBridgeClient(cloud_url, gateway_id, gateway_secret)
        else:
            logger.warning("⚠️ Cloud bridge not configured")
    
    return _bridge_client


async def start_bridge():
    """Start the cloud bridge client."""
    client = get_bridge_client()
    if client:
        logger.info("🚀 Starting cloud bridge client...")
        await client.run()
    else:
        logger.error("❌ Cannot start bridge: not configured")


async def stop_bridge():
    """Stop the cloud bridge client."""
    client = get_bridge_client()
    if client:
        await client.stop()
