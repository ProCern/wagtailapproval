from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem


class ApprovalMenuItem(MenuItem):
    def __init__(self,
        label=_('Approval'), url=reverse_lazy('wagtailapproval:index'),
        classnames='icon icon-tick-inverse', order=200, **kwargs):
        super().__init__(label, url, classnames=classnames, order=order, **kwargs)

    def is_shown(self, request):
        # Fix this to only show for users to whom it is relevant
        return True
