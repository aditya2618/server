from django.apps import AppConfig
import logging
import threading
import asyncio

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Start MQTT client and cloud client when Django starts"""
        print("DEBUG: CoreConfig.ready() STARTED")
        from core.mqtt.client import start_mqtt
        from django.conf import settings
        
        # Start MQTT client (always)
        start_mqtt()
        
        print(f"DEBUG: Checking CLOUD_ENABLED = {getattr(settings, 'CLOUD_ENABLED', False)}")
        
        if getattr(settings, 'CLOUD_ENABLED', False):
            print("DEBUG: Inside CLOUD_ENABLED block!")
            print("DEBUG: About to log info message...")
            logger.info("☁️  Cloud mode enabled - starting cloud client...")
            print("DEBUG: Info message logged!")
            try:
                print("DEBUG: About to import CloudClient...")
                from core.cloud_client import CloudClient
                print("DEBUG: CloudClient imported successfully!")
                
                def run_cloud_client():
                    """Run cloud client in background thread"""
                    try:
                        print("DEBUG: Cloud client thread starting...")
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        client = CloudClient()
                        loop.run_until_complete(client.start())
                        loop.run_forever()
                    except Exception as e:
                        print(f"DEBUG: Cloud client thread error: {e}")
                        logger.error(f"❌ Cloud client thread error: {e}")
                
                print("DEBUG: About to start cloud thread...")
                # Start in daemon thread so it doesn't block Django shutdown
                cloud_thread = threading.Thread(target=run_cloud_client, daemon=True)
                cloud_thread.start()
                print("DEBUG: Cloud thread started successfully!")
            except Exception as e:
                print(f"DEBUG: Exception in cloud client startup: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"❌ Failed to start cloud client: {e}")
        else:
            print("DEBUG: Cloud is DISABLED")
            logger.info("☁️  Cloud mode disabled - local-only mode")
