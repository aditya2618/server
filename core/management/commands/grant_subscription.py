"""
Management command to grant cloud subscription to a home
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Home


class Command(BaseCommand):
    help = 'Grant cloud subscription (basic tier) to a home'

    def add_arguments(self, parser):
        parser.add_argument('home_id', type=int, help='Home ID to grant subscription')
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days until expiration (default: 365)'
        )

    def handle(self, *args, **options):
        home_id = options['home_id']
        days = options['days']

        try:
            home = Home.objects.get(id=home_id)
        except Home.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Home {home_id} not found'))
            return

        # Grant basic subscription
        home.cloud_subscription_tier = 'basic'
        home.cloud_expires_at = timezone.now() + timedelta(days=days)
        home.save()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Granted Basic Cloud subscription to Home {home_id} ({home.name})'
        ))
        self.stdout.write(f'   Expires: {home.cloud_expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
