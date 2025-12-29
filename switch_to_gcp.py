"""
Helper script to switch .env to GCP Cloud
"""
import os
from pathlib import Path

env_path = Path(__file__).parent / '.env'
GCP_IP = "35.209.239.164"
# Assuming standard Django Channel port 8000 for WebSocket
CLOUD_BRIDGE_URL = f"ws://{GCP_IP}:8000/ws/gateway/"

print(f"🔍 Switching .env to GCP Cloud: {GCP_IP}...")

if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    has_bridge_url = False
    
    for line in lines:
        # Update BRIDGE URL
        if line.startswith('CLOUD_BRIDGE_URL'):
            new_lines.append(f'CLOUD_BRIDGE_URL={CLOUD_BRIDGE_URL}\n')
            has_bridge_url = True
            print("✅ Updated CLOUD_BRIDGE_URL")
        # Remove old credentials (force re-pair)
        elif line.startswith('CLOUD_GATEWAY_ID') or line.startswith('CLOUD_GATEWAY_SECRET') or line.startswith('CLOUD_GATEWAY_UUID'):
            print(f"🗑️  Removed old credential: {line.split('=')[0]}")
            continue
        # Keep CLOUD_ENABLED
        elif line.startswith('CLOUD_ENABLED'):
             new_lines.append('CLOUD_ENABLED=True\n')
        else:
            new_lines.append(line)
            
    if not has_bridge_url:
        new_lines.append(f'CLOUD_BRIDGE_URL={CLOUD_BRIDGE_URL}\n')
        print("✅ Added CLOUD_BRIDGE_URL")
        
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
        
    print("\n" + "="*50)
    print("✅ .env updated for GCP Cloud!")
    print("="*50)
    print("\nNext Steps:")
    print(f"1. Run: python quick_pair.py")
    print("2. Run the pair_gateway command it gives you")
    print("3. Restart the server")
else:
    print("❌ .env file not found!")
