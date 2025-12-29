import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Home
from datetime import datetime, timedelta

# Enable subscription for Admin home (ID: 6)
try:
    home = Home.objects.get(id=6)
    home.cloud_subscription_tier = 'basic'
    home.cloud_enabled = False  # User toggles this in app
    home.cloud_expires_at = datetime.now() + timedelta(days=365)
    home.save()
    
    print(f"✅ Cloud subscription enabled for: {home.name} (ID: {home.id})")
    print(f"☁️ Tier: {home.cloud_subscription_tier}")
    print(f"⏰ Expires: {home.cloud_expires_at.strftime('%Y-%m-%d')}")
    print("\n🎉 Ready! Restart the app or pull-to-refresh Settings to see the change.")
except Home.DoesNotExist:
    print(f"❌ Home with ID 6 not found")
