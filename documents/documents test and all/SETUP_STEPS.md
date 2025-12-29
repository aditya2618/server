# Step-by-Step: Local Server Setup & Cloud Pairing

## Step 1: Restart Local Server with WebSocket Support

**Current Issue**: Server needs restart to enable Daphne (WebSocket support)

```bash
# Stop the current server (Ctrl+C in the terminal)
# Then restart:
cd d:\PROJECT\esp32-flasher\server
python manage.py runserver 0.0.0.0:8000
```

**Look for this in startup logs**:
```
Starting ASGI/Daphne development server at http://0.0.0.0:8000/
```
(If you see just "Starting development server" without "ASGI/Daphne", something is wrong)

---

## Step 2: Test WebSocket Connection

After server restarts:
1. Open mobile app (it should auto-reload)
2. Navigate to any screen
3. Check Expo logs for:
   ```
   ✅ WebSocket connected
   ```

If you still see 404 errors, let me know!

---

## Step 3: Pair with Production Cloud (OPTIONAL)

**Only do this if you want remote access through cloud.**

### 3a. Generate Pairing Code

**Option 1 - From Mobile App** (when cloud mode is added):
- Login to mobile
- Request pairing code
- Get 8-digit code

**Option 2 - Via API**:
```bash
# Login to get token
curl -X POST http://35.209.239.164/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'

# Request pairing code (use token from above)
curl -X POST http://35.209.239.164/api/gateways/request-pairing \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"home_name":"My Home","expiry_minutes":10}'
```

### 3b. Pair Local Server

```bash
cd d:\PROJECT\esp32-flasher\server
python manage.py pair_gateway 12345678
```

Replace `12345678` with your actual code.

**Expected output**:
```
🔗 Gateway Pairing
Pairing Code: 12345678
Home ID: xxx-xxx-xxx
Gateway UUID: yyy-yyy-yyy
✅ Gateway paired successfully!
✅ Credentials added to .env file
```

### 3c. Restart Server to Connect to Cloud

```bash
python manage.py runserver 0.0.0.0:8000
```

**Look for**:
```
☁️  Cloud mode enabled - will connect to cloud
✅ Connected to cloud!
```

---

## Current Priority

**FIRST**: Restart server and verify local WebSocket works!

The cloud pairing is optional - your local setup should work perfectly without it. Cloud is only for remote access when you're not on the same WiFi network.
