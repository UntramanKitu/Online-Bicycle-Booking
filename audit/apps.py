from django.apps import AppConfig


class AuditConfig(AppConfig):
    name = 'audit'
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        import audit.signals
