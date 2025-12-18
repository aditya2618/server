# ESP32 Smart Home Platform - Setup Guide

Complete installation and setup instructions for the Django-based ESP32/ESP8266 smart home platform.

## 📋 Prerequisites

- Python 3.11+
- Windows 10/11
- Mosquitto MQTT Broker (already installed in esp32-django project)
- Redis (download from link below)

## 🔧 Step 1: Redis Installation

### Download Redis for Windows
Download and install Redis from:
**https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.msi**

### Installation Steps
1. Run the downloaded MSI installer
2. Follow the installation wizard (use default settings)
3. Redis will be installed as a Windows service and start automatically
4. Default port: `6379`

### Verify Redis is Running
Open PowerShell and run:
```powershell
redis-cli ping
```
**Expected output:** `PONG`

If you get an error, start Redis manually:
```powershell
redis-server
```

---

## 🐍 Step 2: Python Virtual Environment Setup

### Navigate to Server Directory
```powershell
cd h:\aditya\esp32-final\server
```

### Create Virtual Environment (if not exists)
```powershell
python -m venv server
```

### Activate Virtual Environment
```powershell
.\server\Scripts\Activate
```

---

## 📦 Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

**Dependencies installed:**
- Django 5.2.9
- paho-mqtt
- celery
- redis
- django-celery-beat

---

## 🗄️ Step 4: Database Setup

### Run Migrations
```powershell
python manage.py migrate
```

### Create Superuser (for admin access)
```powershell
python manage.py createsuperuser
```
Follow the prompts to set username and password.

---

## 🚀 Step 5: Running the Services

You need to run **3 services** concurrently. Open 3 separate PowerShell windows:

### Terminal 1: Start Redis (if not running as service)
```powershell
redis-server
```

### Terminal 2: Start Celery Worker
```powershell
cd h:\aditya\esp32-final\server
.\server\Scripts\Activate
celery -A smarthome_server worker -l info
```

### Terminal 3: Start Django Server
```powershell
cd h:\aditya\esp32-final\server
.\server\Scripts\Activate
python manage.py runserver
```

### Terminal 4 (Optional): Start MQTT Broker
If Mosquitto is not already running:
```powershell
cd h:\aditya\esp32-final\esp32-django
.\start.ps1
```

---

## 🌐 Access Points

After all services are running:

- **Django Admin:** http://localhost:8000/admin
- **API Toggle Endpoint:** http://localhost:8000/api/entity/<id>/toggle/
- **API Control Endpoint:** http://localhost:8000/api/entity/<id>/control/

---

## 🧪 Testing the System

### 1. Create Test Data
```powershell
python manage.py create_test_data
```

### 2. Test MQTT State Ingestion
Publish a test message:
```powershell
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -t home/1/node_test/sensor/temperature/state -m '{"value":25.5}'
```

### 3. Check Django Logs
You should see in the Django terminal:
```
✓ Updated sensor/temperature on node_test: {'value': 25.5}
```

### 4. Check Celery Logs
You should see automation evaluation in Celery terminal:
```
[INFO] Task core.tasks.evaluate_automations
```

### 5. Verify in Admin Panel
1. Go to http://localhost:8000/admin
2. Login with superuser credentials
3. Check:
   - **Devices** - Auto-created device `node_test`
   - **Entities** - Auto-created entity `temperature`
   - **Entity State History** - State records

---

## 🤖 Creating Automations

### Via Django Admin

1. Navigate to **Admin Panel** → **Automations** → **Add Automation**

2. **Create Automation:**
   - Name: `Turn on fan when hot`
   - Enabled: ✓

3. **Add Trigger:**
   - Entity: `temperature sensor`
   - Operator: `>`
   - Value: `30`

4. **Add Action:**
   - Entity: `fan`
   - Command: `{"state": "ON", "speed": 3}`

5. **Test:**
```powershell
mosquitto_pub -t "home/1/node_1/sensor/temperature/state" -m "32"
```

**Expected Result:**
- Celery logs show automation triggered
- MQTT command published to fan: `{"state":"ON","speed":3}`

---

## 🔍 Health Monitoring

### Check Device Health
Run the health check command to mark stale devices offline:
```powershell
python manage.py device_health_check
```

This checks for devices that haven't sent data in 60 seconds and marks them offline.

---

## 📝 Project Structure

```
server/
├── smarthome_server/          # Django project
│   ├── settings.py           # Configuration
│   ├── celery.py             # Celery app
│   └── urls.py               # URL routing
├── core/                      # Main app
│   ├── models.py             # Data models
│   ├── admin.py              # Admin configuration
│   ├── views.py              # API endpoints
│   ├── tasks.py              # Celery tasks
│   ├── mqtt/                 # MQTT integration
│   │   ├── client.py         # MQTT client
│   │   ├── parser.py         # Topic parser
│   │   └── handlers.py       # Message handlers
│   ├── services/             # Business logic
│   │   └── device_control.py # Device control
│   └── management/commands/  # Management commands
│       ├── create_test_data.py
│       └── device_health_check.py
├── requirements.txt           # Dependencies
└── manage.py                 # Django CLI
```

---

## 🛠️ Troubleshooting

### Redis Connection Error
**Error:** `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution:**
1. Check if Redis is running: `redis-cli ping`
2. Restart Redis service or run `redis-server`

### Celery Worker Not Starting
**Error:** `CRITICAL/MainProcess] Unrecoverable error: ConnectionError`

**Solution:**
1. Ensure Redis is running
2. Check `CELERY_BROKER_URL` in settings.py: `redis://localhost:6379/0`

### MQTT Not Receiving Messages
**Solution:**
1. Check Mosquitto is running
2. Verify Django server logs show: `✓ MQTT connected to 127.0.0.1:1883`
3. Test with: `mosquitto_sub -t "home/#" -v`

### Device Not Auto-Created
**Solution:**
1. Ensure Home with ID=1 exists in database
2. Check MQTT topic format: `home/<home_id>/<node>/<entity_type>/<entity>/state`
3. Check Django logs for errors

---

## 🎯 Quick Start Checklist

- [ ] Redis installed and running (`redis-cli ping` → PONG)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations applied (`python manage.py migrate`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Redis running (Terminal 1)
- [ ] Celery worker running (Terminal 2)
- [ ] Django server running (Terminal 3)
- [ ] Mosquitto broker running
- [ ] Test data created (`python manage.py create_test_data`)
- [ ] Admin panel accessible (http://localhost:8000/admin)

---

## 📚 Features Overview

✅ **MQTT State Ingestion** - ESP32 → Django real-time updates  
✅ **Auto-Discovery** - Zero-config device onboarding  
✅ **Device Control** - Django → ESP32 commands  
✅ **Offline Detection** - LWT + heartbeat monitoring  
✅ **Automation Engine** - Celery-based autonomous rules  
✅ **Admin Panel** - Full CRUD for all models  
✅ **REST API** - Control endpoints for integrations

---

## 🔗 Additional Resources

- **Django Documentation:** https://docs.djangoproject.com/
- **Celery Documentation:** https://docs.celeryq.dev/
- **ESPHome Documentation:** https://esphome.io/
- **MQTT Documentation:** https://mqtt.org/

---

## 📄 License

This project is part of the ESP32 Smart Home Platform.

---

**Need Help?** Check the troubleshooting section or review the Django/Celery logs for detailed error messages.
