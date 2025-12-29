import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Home
from datetime import datetime, timedelta

# Get the first home or create one
home = Home.objects.first()

if not home:
    print("❌ No homes found in database!")
    print("💡 Create a home first through the mobile app")
else:
    # Enable cloud subscription
    home.cloud_subscription_tier = 'basic'
    home.cloud_enabled = False  # User still needs to toggle it manually
    home.cloud_expires_at = datetime.now() + timedelta(days=365)  # 1 year subscription
    home.save()
    
    print("✅ Cloud subscription enabled!")
    print(f"📱 Home: {home.name} (ID: {home.id})")
    print(f"☁️ Tier: {home.cloud_subscription_tier}")
    print(f"⏰ Expires: {home.cloud_expires_at.strftime('%Y-%m-%d')}")
    print(f"🔧 Cloud Mode: {'Enabled' if home.cloud_enabled else 'Disabled (toggle in app)'}")
    print("\n✅ Ready to test! Open the mobile app Settings to toggle cloud mode.")
