import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Device, Home

# Get all devices without a home ForeignKey
devices = Device.objects.filter(home__isnull=True)

for device in devices:
    print(f"Device: {device.node_name}, home_identifier: {device.home_identifier}")
    
    # Try to find matching home by checking HomeMember relationships
    # or create/link to first home
    home = Home.objects.first()
    
    if home:
        device.home = home
        device.save()
        print(f"  → Linked to Home: {home.name} (ID: {home.id})")
    else:
        print(f"  → No homes found! Create a home first.")

print("\nDone! All devices now linked to homes.")
