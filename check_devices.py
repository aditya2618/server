import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_server.settings')
django.setup()

from core.models import Device

devices = Device.objects.all()
for d in devices:
    print(f"Device: {d.node_name}, home_identifier: '{d.home_identifier}', home: {d.home}")
