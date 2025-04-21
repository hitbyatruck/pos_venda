from django.apps import AppConfig


class AssistenciaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'assistencia'

    def ready(self):
        # Register templatetags
        from django.template.defaulttags import register
        try:
            # Import the template tags to make them available
            import assistencia.templatetags.assistencia_extras
        except ImportError:
            pass
