from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.apps import AppConfig


class WagtailApprovalConfig(AppConfig):
    '''Simply imports signals'''
    name = 'wagtailapproval'

    def ready(self):
        from . import _signals  # noqa: F401
