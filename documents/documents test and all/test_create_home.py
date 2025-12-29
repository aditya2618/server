import requests

# Test create home endpoint
url = "http://192.168.29.91:8000/api/homes/"
headers = {
    "Authorization": "Token 799bd3162d7724fdc5f6971223c906d197455d46",
    "Content-Type": "application/json"
}
data = {
    "name": "Python Test Home"
}

response = requests.post(url, json=data, headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 201:
    print("✅ CREATE HOME API WORKS!")
    print(f"Created home: {response.json()['name']}")
    print(f"Home ID: {response.json()['id']}")
else:
    print("❌ CREATE HOME API FAILED!")
