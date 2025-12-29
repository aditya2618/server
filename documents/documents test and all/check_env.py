import os
from dotenv import load_dotenv

load_dotenv()
print(f"CLOUD_ENABLED={os.getenv('CLOUD_ENABLED')}")
print(f"CLOUD_BRIDGE_URL={os.getenv('CLOUD_BRIDGE_URL')}")
print(f"CLOUD_GATEWAY_ID={os.getenv('CLOUD_GATEWAY_ID')}")
print(f"CLOUD_GATEWAY_UUID={os.getenv('CLOUD_GATEWAY_UUID')}")
