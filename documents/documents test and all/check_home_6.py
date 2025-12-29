import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Home

home = Home.objects.get(id=6)
print(f"✅ Home: {home.name} (ID: {home.id})")
print(f"☁️ cloud_subscription_tier: {home.cloud_subscription_tier}")
print(f"🔧 cloud_enabled: {home.cloud_enabled}")
print(f"⏰ cloud_expires_at: {home.cloud_expires_at}")
print(f"\n🔍 has_cloud_access: {home.cloud_subscription_tier != 'free'}")
