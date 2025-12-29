"""
Local Cloud Server Test
"""
import requests

CLOUD_URL = "http://localhost:9000"

print("🌐 Local Cloud Pairing Test")
print("=" * 70)

email = "test@test.com"
password = "testpass123"

# Try register first
print("\n📝 Step 1: Creating test account...")
try:
    response = requests.post(
        f"{CLOUD_URL}/api/auth/register/",
        json={
            "email": email,
            "password": password,
            "password2": password,
            "first_name": "Test",
            "last_name": "User"
        },
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ Account created!")
        data = response.json()
        token = data['access']
        print(f"Token: {token[:50]}...")
        print(f"Homes: {data.get('homes', [])}")
        
        # Request pairing code
        print("\n📡 Step 2: Requesting pairing code...")
        response = requests.post(
            f"{CLOUD_URL}/api/gateways/request-pairing/",
            headers={"Authorization": f"Bearer {token}"},
            json={"home_name": "Test Home", "expiry_minutes": 10},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            code = response.json()['code']
            print("\n" + "=" * 70)
            print(f"✅ PAIRING CODE: {code}")
            print("=" * 70)
            print(f"\nRun: python manage.py pair_gateway {code}")
        else:
            print(f"❌ Failed to get pairing code")
    elif response.status_code == 400:
        print("Account might already exist, trying login...")
        
        # Try login
        response = requests.post(
            f"{CLOUD_URL}/api/auth/login/",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data['access']
            print("✅ Login successful!")
            
            # Request pairing code
            print("\n📡 Requesting pairing code...")
            response = requests.post(
                f"{CLOUD_URL}/api/gateways/request-pairing/",
                headers={"Authorization": f"Bearer {token}"},
                json={"home_name": "Test Home", "expiry_minutes": 10},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 201:
                code = response.json()['code']
                print("\n" + "=" * 70)
                print(f"✅ PAIRING CODE: {code}")
                print("=" * 70)
                print(f"\nRun: python manage.py pair_gateway {code}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
