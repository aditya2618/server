import requests

CLOUD_URL = "http://35.209.239.164"
EMAIL = "bmanpart3@gmail.com"
PASSWORD = "*Aditya2618"

def get_code():
    session = requests.Session()
    
    # Login
    print("Logging in...")
    resp = session.post(f"{CLOUD_URL}/api/auth/login/", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    
    token = resp.json()['access']
    headers = {'Authorization': f'Bearer {token}'}

    # Request code
    print("Requesting pairing code...")
    resp = session.post(
        f"{CLOUD_URL}/api/gateways/request-pairing/", 
        json={"home_name": "Re-Paired Home"},
        headers=headers
    )
    
    if resp.status_code == 201:
        code = resp.json()['code']
        print(f"\n✅ PAIRING CODE: {code}")
        print(f"Run: python manage.py pair_gateway {code}")
    else:
        print(f"Failed to get code: {resp.text}")

if __name__ == '__main__':
    get_code()
