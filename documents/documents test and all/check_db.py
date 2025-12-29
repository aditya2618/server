import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smarthome_server.settings")
django.setup()

from core.models import Entity

try:
    e = Entity.objects.get(id=6)
    print(f"CHECK_DB_RESULT: {e.state}")
except Entity.DoesNotExist:
    print("CHECK_DB_RESULT: Entity 6 not found")
except Exception as e:
    print(f"CHECK_DB_RESULT: Error: {e}")
