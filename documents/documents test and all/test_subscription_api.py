import requests

url = "http://192.168.29.91:8000/api/homes/6/subscription/"
headers = {"Authorization": "Token 799bd3162d7724fdc5f6971223c906d197455d46"}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
