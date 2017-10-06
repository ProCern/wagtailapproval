from django.apps import AppConfig


class WagtailApprovalConfig(AppConfig):
    '''Simply imports signals'''
    name = 'wagtailapproval'

    def ready(self):
        from . import _signals  # noqa: F401
