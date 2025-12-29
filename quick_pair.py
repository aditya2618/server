"""
Cloud Pairing - FIXED for trailing slashes
"""
import requests

CLOUD_URL = "http://35.209.239.164"

print("🌐 Cloud Pairing (with trailing slashes)")
print("=" * 70)

email = "bmanpart3@gmail.com"
password = "*Aditya2618"

# Try login first
print("\n🔐 Attempting login...")
try:
    response = requests.post(
        f"{CLOUD_URL}/api/auth/login/",  # ← Added trailing slash!
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
            f"{CLOUD_URL}/api/gateways/request-pairing/",  # ← Trailing slash!
            headers={"Authorization": f"Bearer {token}"},
            json={"home_name": "Aditya's Smart Home", "expiry_minutes": 10},
            timeout=10
        )
        
        if response.status_code == 201:
            code = response.json()['code']
            print("\n" + "=" * 70)
            print(f"✅ PAIRING CODE: {code}")
            print("=" * 70)
            print("\n📋 To pair your local server:")
            print(f"   1. Open NEW terminal")
            print(f"   2. cd d:\\PROJECT\\esp32-flasher\\server")
            print(f"   3. python manage.py pair_gateway {code}")
            print(f"   4. python manage.py runserver 0.0.0.0:8000")
            print()
            print("Look for: ☁️ Cloud mode enabled ✅ Connected to cloud!")
            print()
        else:
            print(f"❌ Pairing request failed: {response.status_code}")
            print(response.text[:300])
            
    elif response.status_code == 400 or response.status_code == 401:
        print("⚠️  Account doesn't exist. Creating new account...")
        
        # Register
        response = requests.post(
            f"{CLOUD_URL}/api/auth/register/",  # ← Trailing slash!
            json={
                "email": email,
                "password": password,
                "password2": password,
                "first_name": "Aditya",
                "last_name": "Pech"
            },
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Account created! Re-running login...")
            
            # Login again
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
                print("\n� Requesting pairing code...")
                response = requests.post(
                    f"{CLOUD_URL}/api/gateways/request-pairing/",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"home_name": "Aditya's Smart Home", "expiry_minutes": 10},
                    timeout=10
                )
                
                if response.status_code == 201:
                    code = response.json()['code']
                    print("\n" + "=" * 70)
                    print(f"✅ PAIRING CODE: {code}")
                    print("=" * 70)
                    print(f"\nRun: python manage.py pair_gateway {code}")
                    print()
                else:
                    print(f"❌ Pairing failed: {response.text[:300]}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(response.text[:300])
    else:
        print(f"❌ Unexpected error: {response.status_code}")
        print(response.text[:300])

except Exception as e:
    print(f"❌ Error: {e}")
