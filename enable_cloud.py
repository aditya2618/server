"""
Helper script to enable cloud mode in .env file
"""
import os
from pathlib import Path

# Get .env path
env_path = Path(__file__).parent / '.env'

print("🔍 Checking .env file for CLOUD_ENABLED...")

# Read current .env
if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Check if CLOUD_ENABLED exists
    found = False
    new_lines = []
    
    for line in lines:
        if line.startswith('CLOUD_ENABLED'):
            found = True
            new_lines.append('CLOUD_ENABLED=True\n')
            print(f"✅ Updated existing: CLOUD_ENABLED=True")
        else:
            new_lines.append(line)
    
    # If not found, add it
    if not found:
        new_lines.append('\n# Cloud Bridge\nCLOUD_ENABLED=True\n')
        print("✅ Added: CLOUD_ENABLED=True")
    
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print("\n" + "="*50)
    print("✅ Cloud mode ENABLED in .env")
    print("="*50)
    print("\n⚠️  IMPORTANT: You MUST restart the server:")
    print("   1. Stop the current 'python manage.py runserver' (Ctrl+C)")
    print("   2. Run: python manage.py runserver 0.0.0.0:8000")
    print("\nThe server will then:")
    print("   ☁️  Start the cloud bridge client")
    print("   🔌 Connect to the cloud WebSocket")
    print("   ✅ Enable remote device control")
else:
    print("❌ .env file not found!")
    print("Creating .env with CLOUD_ENABLED=True...")
    with open(env_path, 'w') as f:
        f.write('CLOUD_ENABLED=True\n')
    print("✅ Created .env with cloud mode enabled")
