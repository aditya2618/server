from channels.generic.websocket import AsyncJsonWebsocketConsumer


class HomeConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time home state updates.
    
    Each home gets its own channel group. All connected clients receive:
    - Entity state changes (sensor readings, switch states, etc.)
    - Device online/offline status updates
    
    Connection URL: ws://server/ws/home/<home_id>/
    """
    
    async def connect(self):
        """
        Called when WebSocket connection is established.
        
        Authenticates user via token in query string,
        extracts home_id from URL, joins the home's channel group,
        and accepts the connection.
        """
        print("=== WebSocket connect() called ===")
        
        # Get token from query string
        from channels.db import database_sync_to_async
        from rest_framework.authtoken.models import Token
        from django.contrib.auth.models import AnonymousUser
        
        query_string = self.scope.get("query_string", b"").decode()
        token_key = None
        
        print(f"Query string: {query_string}")
        
        # Parse token from query string
        for param in query_string.split("&"):
            if param.startswith("token="):
                token_key = param.split("=")[1]
                break
        
        # Authenticate user
        if token_key:
            try:
                @database_sync_to_async
                def get_user_from_token(key):
                    token = Token.objects.get(key=key)
                    return token.user
                
                user = await get_user_from_token(token_key)
                self.scope["user"] = user
            except Token.DoesNotExist:
                print(f"✗ WebSocket auth failed: Invalid token")
                await self.close()
                return
            except Exception as e:
                print(f"✗ WebSocket auth error: {e}")
                await self.close()
                return
        else:
            print(f"✗ WebSocket auth failed: No token provided")
            await self.close()
            return
        
        # Get home_id from URL
        self.home_id = self.scope["url_route"]["kwargs"]["home_id"]
        self.group_name = f"home_{self.home_id}"

        # Join home-specific group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"✓ WebSocket connected: home_{self.home_id} (user: {self.scope['user'].username})")

    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed.
        
        Removes this connection from the home's channel group.
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"✗ WebSocket disconnected: home_{self.home_id}")

    async def send_state_update(self, event):
        """
        Receives messages from channel layer and sends to WebSocket client.
        
        Called when MQTT handlers broadcast state changes to the group.
        
        Message format from MQTT handlers:
        {
            "type": "send_state_update",
            "data": {
                "type": "entity_state" | "device_status",
                "entity_id": int,
                "state": dict,
                "device_id": int,
                "is_online": bool
            }
        }
        """
        await self.send_json(event["data"])
