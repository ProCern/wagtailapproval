from django.conf.urls import include, url
from wagtail.wagtailcore import hooks

from . import urls
from .menu import ApprovalMenuItem
from .models import ApprovalStep


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^approval/', include(urls)),
        ]

@hooks.register('register_admin_menu_item')
def register_admin_menu_item():
    return ApprovalMenuItem()

@hooks.register('after_create_page')
def take_ownership_if_necessary(request, page):
    '''Checks the request user and takes ownership of the page if it is created
    by an owned user'''
    user = request.user
    for step in ApprovalStep.objects.all():
        group = step.owned_group
        if group in user.groups.all():
            step.take_ownership(page)
            step.save()
