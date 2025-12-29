
import os
import django
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Device, Home, Entity

print(f"Total Homes: {Home.objects.count()}")
for home in Home.objects.all():
    print(f"Home: {home.name} (ID: {home.id}, UUID: {getattr(home, 'identifier', 'N/A')})")
    
print(f"\nTotal Devices: {Device.objects.count()}")
for device in Device.objects.all():
    print(f"Device: {device.name} (ID: {device.id})")
    print(f"  - Home ID: {device.home_id}")
    print(f"  - Home Identifier: {device.home_identifier}")
    print(f"  - Entities: {device.entities.count()}")

print(f"\nTotal Entities: {Entity.objects.count()}")
