from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem

from .models import ApprovalStep

class ApprovalMenuItem(MenuItem):
    def __init__(self,
        label=_('Approval'), url=reverse_lazy('wagtailapproval:index'),
        classnames='icon icon-tick-inverse', order=200, **kwargs):
        super().__init__(label, url, classnames=classnames, order=order, **kwargs)

    def is_shown(self, request):
        user = request.user
        user_groups = user.groups.all()
        for step in ApprovalStep.objects.all():
            if step.owned_group in user_groups:
                return True
        return False
