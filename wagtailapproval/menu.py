from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.menu import MenuItem

class ApprovalMenuItem(MenuItem):
    # Fix the url selection, instead using a reverse_lazy
    def __init__(self, label=_('Approval'), url='/approvals',
                 classnames='icon icon-tick-inverse', order=250, **kwargs):
        super().__init__(label, url, classnames=classnames, order=order, **kwargs)

    def is_shown(self, request):
        # Fix this to only show for users to whom it is relevant
        return True
