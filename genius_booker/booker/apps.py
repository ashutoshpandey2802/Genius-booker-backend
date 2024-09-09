from django.apps import AppConfig

class BookerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booker'

    def ready(self):
        # Import the signals module
        import booker.signals
