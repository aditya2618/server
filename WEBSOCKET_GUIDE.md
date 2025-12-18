# WebSocket Quick Start Guide

## 🚀 Quick Start (4 Commands)

```bash
# Terminal 1 - Redis
redis-server

# Terminal 2 - Celery Worker
cd h:\aditya\esp32-final\server
.\server\Scripts\Activate.ps1
celery -A smarthome_server worker -l info

# Terminal 3 - Celery Beat
cd h:\aditya\esp32-final\server
.\server\Scripts\Activate.ps1
celery -A smarthome_server beat -l info

# Terminal 4 - Django Server
cd h:\aditya\esp32-final\server
.\server\Scripts\Activate.ps1
python manage.py runserver
```

## 🧪 Test WebSocket

Open in browser: `file:///h:/aditya/esp32-final/server/test_websocket.html`

Or use browser console:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/home/1/');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

## 📡 WebSocket Endpoint

```
ws://localhost:8000/ws/home/<home_id>/
```

## 📨 Message Types

### Entity State Update
```json
{
  "type": "entity_state",
  "entity_id": 12,
  "state": {"value": "ON", "brightness": 70},
  "device_id": 3,
  "is_online": true
}
```

### Device Status Update
```json
{
  "type": "device_status",
  "device_id": 3,
  "is_online": false
}
```

## 🔧 Troubleshooting

**Connection Refused?**
- Check all 4 services are running
- Verify Redis: `redis-cli ping` → should return `PONG`

**No Messages?**
- Check MQTT broker is running
- Verify ESP32 is publishing messages
- Check Django console for MQTT connection logs

## 📱 Android Integration

```kotlin
val ws = OkHttpClient().newWebSocket(
    Request.Builder().url("ws://192.168.1.100:8000/ws/home/1/").build(),
    object : WebSocketListener() {
        override fun onMessage(webSocket: WebSocket, text: String) {
            val data = JSONObject(text)
            // Update UI based on data.getString("type")
        }
    }
)
```

## 🌐 Production Deployment

Replace `python manage.py runserver` with:
```bash
pip install daphne
daphne -b 0.0.0.0 -p 8000 smarthome_server.asgi:application
```
