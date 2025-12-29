"""
Detailed Cloud Pairing Test
"""
import requests
import json

CLOUD_URL = "http://35.209.239.164"

print("🌐 Detailed Cloud Pairing Test")
print("=" * 70)

email = "bmanpart3@gmail.com"
password = "*Aditya2618"

# Try login first
print("\n🔐 Step 1: Attempting login...")
try:
    response = requests.post(
        f"{CLOUD_URL}/api/auth/login/",
        json={"email": email, "password": password},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text[:1000]}")
    
    if response.status_code == 200:
        data = response.json()
        token = data['access']
        print("✅ Login successful!")
        print(f"Token (first 50 chars): {token[:50]}...")
        print(f"Homes: {data.get('homes', [])}")
        
        # Request pairing code
        print("\n📡 Step 2: Requesting pairing code...")
        response = requests.post(
            f"{CLOUD_URL}/api/gateways/request-pairing/",
            headers={"Authorization": f"Bearer {token}"},
            json={"home_name": "Aditya's Smart Home", "expiry_minutes": 10},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 201:
            code = response.json()['code']
            print("\n" + "=" * 70)
            print(f"✅ PAIRING CODE: {code}")
            print("=" * 70)
        else:
            print(f"❌ Failed to get pairing code")
            
    elif response.status_code in [400, 401, 404]:
        print(f"⚠️  Login failed - trying registration...")
        
        # Register
        print("\n📝 Step 2: Creating account...")
        response = requests.post(
            f"{CLOUD_URL}/api/auth/register/",
            json={
                "email": email,
                "password": password,
                "password2": password,
                "first_name": "Aditya",
                "last_name": "Pech"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:1000]}")
        
        if response.status_code == 201:
            print("✅ Account created! Now login and run again.")
        else:
            print(f"❌ Registration failed")
    else:
        print(f"❌ Unexpected status code")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
