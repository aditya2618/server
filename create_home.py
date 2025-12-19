"""
Quick script to create a Home with ID=1 for testing MQTT auto-discovery
"""
from django.contrib.auth.models import User
from core.models import Home

# Get or create admin user
user = User.objects.filter(is_superuser=True).first()
if not user:
    print("No superuser found. Please create one first.")
    exit(1)

# Create Home with ID=1
home, created = Home.objects.get_or_create(
    id=1,
    defaults={
        "name": "My Smart Home",
        "owner": user
    }
)

if created:
    print(f"✅ Created Home: {home.name} (ID={home.id})")
else:
    print(f"✅ Home already exists: {home.name} (ID={home.id})")

print("\n📡 Now you can test MQTT with:")
print('mosquitto_pub -t "home/1/test_node/sensor/temperature/state" -m \'{"value": 25.5}\'')
