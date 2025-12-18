from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Start MQTT client when Django starts"""
        from core.mqtt.client import start_mqtt
        start_mqtt()
