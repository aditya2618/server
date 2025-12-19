"""
Management command to clean up old entity state history records.
Run this daily via cron/task scheduler or django-celery-beat.
"""
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from core.models import EntityStateHistory


class Command(BaseCommand):
    help = 'Delete entity state history older than specified days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete records older than this many days (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = now() - timedelta(days=days)
        
        # Query old records
        old_records = EntityStateHistory.objects.filter(
            timestamp__lt=cutoff_date
        )
        
        count = old_records.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} records older than {days} days'
                )
            )
        else:
            old_records.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Deleted {count} history records older than {days} days'
                )
            )
