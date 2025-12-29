import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Home

home = Home.objects.first()
if home:
    try:
        print(f"✅ cloud_enabled: {home.cloud_enabled}")
        print(f"✅ cloud_subscription_tier: {home.cloud_subscription_tier}")
        print(f"✅ cloud_expires_at: {home.cloud_expires_at}")
        print("\n✅ Migration applied successfully! Database has subscription fields.")
    except AttributeError as e:
        print(f"❌ Fields missing: {e}")
        print("⚠️ Migration NOT applied yet.")
else:
    print("⚠️ No homes in database to test")
