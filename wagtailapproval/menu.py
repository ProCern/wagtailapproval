from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from django.contrib.auth import get_user
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy as _n
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.menu import MenuItem

from .approvalitem import get_user_approval_items
from .models import ApprovalStep


class ApprovalMenuItem(MenuItem):
    '''The menu item that shows in the wagtail sidebar'''

    def __init__(
        self,
        label=_('Approval'), url=reverse_lazy('wagtailapproval:index'),
        classnames='icon icon-tick-inverse', order=200, **kwargs):
        super(ApprovalMenuItem, self).__init__(
            label,
            url,
            classnames=classnames,
            order=order,
            **kwargs)

    def is_shown(self, request):
        '''Only show the menu if the user is in an owned approval group'''
        user = get_user(request)
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
