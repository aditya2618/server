"""
Django management command to start the cloud bridge client.
Usage: python manage.py start_cloud_bridge
"""
import asyncio
from django.core.management.base import BaseCommand
from core.services.cloud_bridge_client import start_bridge


class Command(BaseCommand):
    help = 'Start the cloud bridge client for remote access'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Cloud Bridge Client...'))
        self.stdout.write('Press Ctrl+C to stop')
        
        try:
            asyncio.run(start_bridge())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n🛑 Bridge client stopped by user'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Bridge client error: {e}'))
