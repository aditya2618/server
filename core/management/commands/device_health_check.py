from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from core.models import Device


class Command(BaseCommand):
    help = "Mark devices offline if heartbeat expired (no activity for 60 seconds)"

    def handle(self, *args, **kwargs):
        threshold = now() - timedelta(seconds=60)

        # Find devices that are marked online but haven't been seen recently
        stale_devices = Device.objects.filter(
            is_online=True,
            last_seen__lt=threshold
        )

        count = stale_devices.count()
        
        if count > 0:
            # Mark them offline
            stale_devices.update(is_online=False)
            self.stdout.write(
                self.style.WARNING(f'Marked {count} device(s) offline due to heartbeat timeout')
            )
            
            # List affected devices
            for device in stale_devices:
                self.stdout.write(f'  - {device.name} ({device.node_name})')
        else:
            self.stdout.write(
                self.style.SUCCESS('All devices are healthy')
            )
