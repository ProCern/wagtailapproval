from django.apps import AppConfig

class WagtailApprovalConfig(AppConfig):
    name = 'wagtailapproval'
    def ready(self):
        from . import signals
