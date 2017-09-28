from django.conf.urls import include, url
from wagtail.wagtailcore import hooks

from . import urls
from .menu import ApprovalMenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^approval/', include(urls)),
        ]

@hooks.register('register_admin_menu_item')
def register_admin_menu_item():
    return ApprovalMenuItem()
