"""
End-to-End Cloud Control Test
Tests the full path: Script -> Cloud -> Gateway -> Device
"""
import requests
import json
import time

CLOUD_URL = "http://35.209.239.164"
EMAIL = "bmanpart3@gmail.com"
PASSWORD = "*Aditya2618"

def test_e2e():
    print("🚀 Starting End-to-End Cloud Verification")
    print("=" * 60)

    # 1. Login
    print("\n🔐 1. Logging in to Cloud...")
    try:
        resp = requests.post(f"{CLOUD_URL}/api/auth/login/", json={
            "email": EMAIL,
            "password": PASSWORD
        }, timeout=10)
        
        if resp.status_code != 200:
            print(f"❌ Login failed: {resp.text}")
            return
            
        token = resp.json()['access']
        print("✅ Login successful")
        
        homes = resp.json().get('homes', [])
        if not homes:
            print("❌ No homes found for user")
            # Try to fetch homes explicitly if not in login response
            return
            
        # Check if homes is list of strings or objects
        first_home = homes[0]
        if isinstance(first_home, str):
            home_id = first_home
        else:
            home_id = first_home['id']
            
        print(f"🏠 Using Home ID: {home_id}")

        # 2. Get Devices
        print(f"\n📱 2. Fetching devices for home {home_id}...")
        headers = {"Authorization": f"Bearer {token}"}
        
        import time
        max_retries = 10
        devices = []
        
        for i in range(max_retries):
            resp = requests.get(f"{CLOUD_URL}/api/homes/{home_id}/devices/", headers=headers, timeout=10)
            
            if resp.status_code != 200:
                print(f"❌ Failed to get devices: {resp.text}")
                return
                
            data = resp.json()
            # Handle pagination
            if isinstance(data, dict) and 'results' in data:
                devices = data['results']
            elif isinstance(data, list):
                devices = data
            else:
                devices = [] # Unexpected format
            
            print(f"RAW DEVICES (Attempt {i+1}): {data}")
            
            if len(devices) > 0:
                print(f"✅ Found {len(devices)} devices/entities")
                break
                
            print("⏳ Waiting for sync...")
            time.sleep(3)
            
        else:
             print("❌ Timeout: Devices did not sync.")
             return
        for d in devices:
            if isinstance(d, str):
                print(f"  - String device? {d}")
                continue
            print(f"   - [{d['id']}] {d['name']} ({d['entity_type']}): {d.get('state')}")
            
        # Find a light to toggle
        target_light = None
        for d in devices:
            if d['entity_type'] in ['switch', 'light']:
                target_light = d
                break
                
        if not target_light:
            print("\n⚠️ No light/switch found to test control.")
            return

        # 3. Toggle Device
        cmd = 'off' if target_light.get('state', {}).get('value') else 'on'
        val = False if cmd == 'off' else True
        
        print(f"\n⚡ 3. Toggling {target_light['name']} (ID: {target_light['id']}) to {cmd.upper()}...")
        
        control_url = f"{CLOUD_URL}/api/homes/{home_id}/devices/{target_light['id']}/control/"
        payload = {
            "command": "turn_on" if val else "turn_off", # Adjust based on your API spec
            #"value": val 
        }
        # Based on previous context, the API might expect 'state' or specific action
        # Let's try the standard pattern previously seen or check API def via experimentation
        # Usually: POST /api/homes/{home_id}/devices/{entity_id}/state/ or similar?
        # Let's check the CloudClient handle_control_command to see what it expects.
        # It expects: command, value. 
        # The Mobile App calls: POST /api/homes/:homeId/entities/:entityId/control 
        # Body: { command: "update_state", value: ... } or similar.
        
        # Let's try generic update first
        payload = {
            "command": "update_state", 
            "value": val
        }
        
        resp = requests.post(control_url, json=payload, headers=headers, timeout=10)
        print(f"Response: {resp.status_code} - {resp.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_e2e()
