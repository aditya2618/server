# Cloud Mode Debugging Summary
**Date**: 2025-12-28  
**Session Duration**: ~1.5 hours

## 🎯 Objective
Enable remote device control via cloud when mobile app is on mobile data (4G/5G), away from local WiFi network.

## ✅ What's Working

### Local Server
- ✅ MQTT client running
- ✅ Devices connected and reporting states
- ✅ Automations working
- ✅ Local control (WiFi) works perfectly

### Cloud Infrastructure
- ✅ GCP server running at `35.209.239.164`
- ✅ Local gateway connects to cloud bridge
- ✅ Gateway syncs 4 devices to cloud
- ✅ WebSocket connection established
- ✅ Cloud logs show: `✅ Gateway connected: 96fd8064-c31b-4008-92ed-0c6361351783`

### Mobile App
- ✅ Cloud mode toggle in Settings works
- ✅ Network mode detection logic implemented
- ✅ Fixed `controlEntity` to use `cloudApi` instead of `wsClient` in cloud mode
- ✅ App correctly detects "Cloud Mode" when cloud preference is enabled

## 🔴 Current Blocker: Home ID Type Mismatch

### The Problem
Mobile app and cloud API use different ID formats:

**Mobile App Side:**
- Stores local home ID as **integer**: `1`
- Sends to cloud: `GET /remote/homes/1/status`

**Cloud API Side:**
- Expects **UUID** (gateway ID): `148d207f-e40b-495a-aab1-79dac65d95df`
- URL pattern: `path('homes/<uuid:home_id>/...', ...)`

**Result:**
```
GET /remote/homes/1/status
→ 404 Not Found (path doesn't match UUID pattern)
→ cloudReachable=false
→ mode=OFFLINE
→ Control commands fail
```

### Why This Happens
1. Local server has integer `home_id=1` in database
2. Mobile app stores and uses this integer
3. Cloud server uses **gateway UUID** as the home identifier
4. When app switches to cloud mode, it sends integer instead of UUID
5. Cloud routes require UUID format, so request fails

## 🔧 Attempted Fixes

### Fix #1: Change URL patterns to accept integers ✅
**File**: `cloud/remote_control/urls.py`

Changed:
```python
path('homes/<uuid:home_id>/...')  # Before
path('homes/<int:home_id>/...')   # After
```

**Status**: ✅ URLs now accept integers

### Fix #2: Update views to map integer → UUID (IN PROGRESS)
**Files**: `cloud/remote_control/views.py`

**Need to**:
- Look up gateway from integer home ID
- Map: `home_id (int) → gateway (UUID)`

## 📊 Data Flow Analysis

### Working Flow (WiFi/Local)
```
Mobile App (WiFi)
  ↓ http://192.168.29.91:8000/api/entities/6/control
Local Server
  ↓ MQTT
ESP32 Device ✅
```

### Broken Flow (Mobile Data/Cloud)
```
Mobile App (4G)
  ↓ GET /remote/homes/1/status (404)
  ↓ cloudReachable=false → mode=OFFLINE
  ↓ POST http://192.168.29.91:8000/api/... (Network Error)
❌ Fails - can't reach 192.168.29.91 on mobile data
```

### Desired Flow (Mobile Data/Cloud)
```
Mobile App (4G)
  ↓ GET /remote/homes/<GATEWAY_UUID>/status ✅
  ↓ cloudReachable=true → mode=CLOUD
  ↓ POST /remote/homes/<GATEWAY_UUID>/entities/6/control
Cloud Server (35.209.239.164)
  ↓ WebSocket
Local Server (192.168.29.91)
  ↓ MQTT
ESP32 Device ✅
```

## 🎯 Next Steps to Complete

### 1. Update Cloud Views (CRITICAL)
**File**: `cloud/remote_control/views.py`

Add logic to look up gateway from local home ID:

```python
def control_entity(request, home_id, entity_id):
    # home_id is now an integer
    # Need to find the gateway that owns this local home
    
    # Option A: Query Gateway by a stored local_home_id field
    gateway = Gateway.objects.get(local_home_id=home_id, ...)
    
    # Option B: Query through permissions
    permission = HomePermission.objects.get(
        user=request.user,
        local_home_id=home_id  # Need to add this field
    )
    gateway = permission.gateway
    
    # Rest of the logic remains the same
```

### 2. Add Local Home ID Field to Models
**Files**: 
- `cloud/gateways/models.py` (Gateway or HomePermission)

Add field to store the local server's integer home ID:
```python
local_home_id = models.IntegerField(null=True, db_index=True)
```

### 3. Sync Local Home ID During Pairing
**File**: Cloud pairing/gateway registration

When gateway registers, send its local home ID:
```python
{
    "gateway_id": "uuid",
    "local_home_id": 1,  # ← Add this
    ...
}
```

### 4. Alternative: Use Gateway UUID in Mobile App
Instead of mapping, have mobile app use gateway UUID directly:

**File**: `mobile/src/api/cloudClient.ts`

Fetch and store gateway UUID:
```typescript
// Get gateway UUID for this home
const gatewayInfo = await cloudApi.getGatewayForHome(homeId);
const gatewayUuid = gatewayInfo.gateway_id;

// Use UUID for cloud calls
await cloudApi.controlEntity(gatewayUuid, entityId, command);
```

## 📝 Configuration Reference

### Environment Variables
**Local Server** (`server/.env`):
```
CLOUD_ENABLED=True
CLOUD_BRIDGE_URL=ws://35.209.239.164/ws/gateway/
CLOUD_GATEWAY_ID=148d207f-e40b-495a-aab1-79dac65d95df
CLOUD_GATEWAY_UUID=96fd8064-c31b-4008-92ed-0c6361351783
CLOUD_GATEWAY_SECRET=a_1rIDkJtEF-kz-hh6p4-4Qfu4DgM01x-wsvLI0siVE
```

### Mobile App Constants
**File**: `mobile/src/api/cloudClient.ts`
```typescript
const CLOUD_URL = 'http://35.209.239.164';
```

### Network IPs
- **Local Server**: `192.168.29.91:8000`
- **GCP Cloud**: `35.209.239.164`

## 🔍 Debugging Commands

### Check Cloud Logs (GCP)
```bash
sudo journalctl -u daphne -f
```

### Check Local Server Logs
Look for:
```
DEBUG: Cloud thread started successfully!
☁️  Connecting to cloud: ws://35.209.239.164/ws/gateway/
✅ Connected to cloud bridge
```

### Check Mobile App Console (Expo)
Key logs:
```
🔍 DETECT: homeId=1, cloudPref=true
🔍 DETECT: localAvailable=false
🔍 DETECT: cloudReachable=false  ← Problem!
⚠️ Network mode: OFFLINE          ← Wrong!
```

## 🐛 Known Issues

1. **Gateway Connection Unstable**: Disconnects every ~30 seconds (might be heartbeat issue)
2. **Missing Status Endpoint**: Mobile app looks for `/api/remote/homes/1/status` but gets 404
3. **Home ID Type Mismatch**: The blocker described above

## 📚 Related Files Modified

### Server
- `server/core/apps.py` - Added debug logging for cloud client
- `server/.env` - Cloud credentials

### Cloud
- `cloud/remote_control/urls.py` - Changed UUID to int
- `cloud/remote_control/views.py` - (Needs update)

### Mobile
- `mobile/src/api/smartClient.ts` - Fixed to use cloudApi in cloud mode
- `mobile/src/api/networkMode.ts` - Network detection logic

---

**Next Session**: Continue with Step 1 (Update Cloud Views) to complete the fix.
