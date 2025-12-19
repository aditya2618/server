# API Testing Results

## Authentication Token

**User:** admin1  
**Token:** `5b626481c48ad948a81805b52937d357a541e8d2`

Use this token for all API requests:
```
Authorization: Token 5b626481c48ad948a81805b52937d357a541e8d2
```

## API Endpoints Tested

### 1. List Homes
**Endpoint:** GET `/api/homes/`  
**Status:** Testing...

### 2. List Devices  
**Endpoint:** GET `/api/homes/1/devices/`  
**Status:** Testing...

### 3. Control Entity
**Endpoint:** POST `/api/entities/1/control/`  
**Body:**
```json
{
  "state": "ON",
  "brightness": 90
}
```
**Status:** Testing...

## PowerShell Test Commands

### Test Homes API
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/homes/" `
  -Headers @{"Authorization"="Token 5b626481c48ad948a81805b52937d357a541e8d2"} `
  -Method GET -UseBasicParsing
```

### Test Devices API
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/homes/1/devices/" `
  -Headers @{"Authorization"="Token 5b626481c48ad948a81805b52937d357a541e8d2"} `
  -Method GET -UseBasicParsing
```

### Test Control API
```powershell
$body = '{"state":"ON","brightness":90}'
Invoke-WebRequest -Uri "http://localhost:8000/api/entities/1/control/" `
  -Headers @{"Authorization"="Token 5b626481c48ad948a81805b52937d357a541e8d2";"Content-Type"="application/json"} `
  -Method POST -Body $body -UseBasicParsing
```
