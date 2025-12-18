"""
WebSocket Test Client

This script tests the WebSocket connection to verify real-time message delivery.

Usage:
    python test_websocket.py

Requirements:
    pip install websocket-client
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/home/1/"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected successfully!")
            print("Waiting for messages from server...")
            print("(Trigger MQTT state changes to see updates)\n")
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                print(f"📨 Received message:")
                print(json.dumps(data, indent=2))
                print()
                
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nMake sure:")
        print("  1. Django server is running (python manage.py runserver)")
        print("  2. Redis is running")
        print("  3. Home with ID=1 exists in database")

if __name__ == "__main__":
    asyncio.run(test_websocket())
