from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import itertools

from django.contrib.auth import get_user
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy as _n
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.menu import MenuItem

from .models import ApprovalStep


def get_user_approval_items(user):
    '''Get an iterable of all items pending for a user's approval.

    :param User user: A user object whose groups are to be checked for
        appropriate steps
    :rtype: Iterable[ApprovalItem]
    :returns: All the items that this user can approve or reject.
    '''

    if user.is_superuser:
        steps = ApprovalStep.objects.all()
    else:
        groups = user.groups.all()
        steps = ApprovalStep.objects.filter(group__in=groups)
    return itertools.chain.from_iterable(
        step.get_items(user) for step in steps)


class ApprovalMenuItem(MenuItem):
    '''The menu item that shows in the wagtail sidebar'''

    def __init__(
        self, label=_('Approval'), url=reverse_lazy('wagtailapproval:index'),
        classnames='icon icon-tick-inverse', order=201, **kwargs):

        super(ApprovalMenuItem, self).__init__(
            label,
            url,
            classnames=classnames,
            order=order,
            **kwargs)

    def is_shown(self, request):
        '''Only show the menu if the user is in an owned approval group'''
        user = get_user(request)
        # If the user is superuser, show the menu if any steps exist at all
        if user.is_superuser:
            return ApprovalStep.objects.exists()

        groups = user.groups.all()
        if ApprovalStep.objects.filter(group__in=groups).exists():
            # Display the approval notification only outside of the approval
            # paths
            if not request.path.startswith(reverse('wagtailapproval:index')):
                # Get the count of waiting approvals
                waiting_approvals = sum(
                    1 for _ in get_user_approval_items(user))
                if waiting_approvals > 0:
                    messages.info(
                        request,
                        _n(
                            '{num:d} item waiting for approval',
                            '{num:d} items waiting for approval',
                            waiting_approvals).format(num=waiting_approvals),
                        buttons=[
                            messages.button(
                                reverse('wagtailapproval:index'),
                                _('Examine Now'))
                        ]
                    )
            return True
        return False


class ApprovalAdminMenuItem(MenuItem):
    '''The admin menu item that shows in the wagtail sidebar, for
    administrating entire pipelines and manually dropping items into steps.'''

    def __init__(
        self, label=_('Approval Admin'),
        url=reverse_lazy('wagtailapproval:admin_index'),
        classnames='icon icon-cog', order=200, **kwargs):
        super(ApprovalAdminMenuItem, self).__init__(
            label,
            url,
            classnames=classnames,
            order=order,
            **kwargs)

    def is_shown(self, request):
        '''Only show the menu if the user is a superuser and any ApprovalStep
        objects exist.'''
        user = get_user(request)
        if user.is_superuser:
            return ApprovalStep.objects.exists()
        return False
