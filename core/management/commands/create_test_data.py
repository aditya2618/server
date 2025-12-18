from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Home, Device, Entity


class Command(BaseCommand):
    help = 'Create test data for MQTT testing'

    def handle(self, *args, **options):
        # Create or get user
        user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com"}
        )

        # Create home
        home, _ = Home.objects.get_or_create(
            id=1,
            defaults={"name": "Test Home", "owner": user}
        )

        # Create device
        device, _ = Device.objects.get_or_create(
            node_name="node_1",
            defaults={
                "home": home,
                "name": "Test ESP32 Node 1"
            }
        )

        # Create test sensor entity
        entity, _ = Entity.objects.get_or_create(
            device=device,
            name="test",
            defaults={
                "entity_type": "sensor",
                "subtype": "dht22",
                "is_controllable": False
            }
        )

        self.stdout.write(self.style.SUCCESS('✓ Test data created:'))
        self.stdout.write(f'  Home: {home}')
        self.stdout.write(f'  Device: {device} (node_name={device.node_name})')
        self.stdout.write(f'  Entity: {entity}')
        self.stdout.write('')
        self.stdout.write('Test MQTT with:')
        self.stdout.write('  mosquitto_pub -t "home/1/node_1/sensor/test/state" -m \'{"temperature":25.6,"humidity":62}\'')
