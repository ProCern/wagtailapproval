from django.conf.urls import include, url
from wagtail.wagtailcore import hooks

from . import urls
from .menu import ApprovalMenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^approval/', include(urls)),
        ]

@hooks.register('construct_main_menu')
def construct_main_menu(request, menu_items):
    menu_items.append(ApprovalMenuItem())
